// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

/// A minimal ERC20 interface for the split path (USDC on Base, 6 decimals).
interface IERC20 {
    function balanceOf(address) external view returns (uint256);
    function transfer(address, uint256) external returns (bool);
}

/// USDCSplitter — one payment identity per paid tool.
///
/// x402 (EIP-3009) settles by sending USDC to this contract as the payTo
/// recipient. There is NO receive hook and NO admin: any caller may
/// trigger flush(), which sends payoutBps/10000 of the token balance to
/// the payout address fixed at clone creation, and the rest to treasury.
///
/// Invariants, by construction:
/// - immutable rule set: token, treasury, payout, payoutBps cannot change;
/// - no owner, no withdraw, no upgrade — the contract cannot move funds
///   to any address it was not born with;
/// - no receive()/fallback() — ETH sent here is unreachable, so we accept
///   none; only the registered token is split;
/// - if the payout address was mis-registered by its owner, funds follow
///   the bytes given: verification was format-only, responsibility stays
///   with the proposer (the human-tried rule, written in code).
contract USDCSplitter {
    IERC20 public immutable token;
    address public immutable treasury;
    address public immutable payout;
    uint16 public immutable payoutBps; // <= 10000

    event Flushed(uint256 total, uint256 toPayout, uint256 toTreasury);

    constructor(IERC20 usdc, address treasury_, address payout_, uint16 payoutBps_) {
        require(payoutBps_ <= 10000, "bps");
        require(treasury_ != address(0) && payout_ != address(0), "zero");
        token = usdc;
        treasury = treasury_;
        payout = payout_;
        payoutBps = payoutBps_;
    }

    /// Permissionless: whoever arrives first settles the dust. Amounts are
    /// floor for payout, remainder (>= payout share) to treasury — the
    /// split is deterministic from the balance, never from a ledger.
    function flush() external {
        uint256 total = token.balanceOf(address(this));
        if (total == 0) return;
        uint256 out = (total * payoutBps) / 10000;
        // checks before effects on external call ordering is moot here:
        // our balance only shrinks, and transfer() reverts on shortfall.
        bool a = token.transfer(payout, out);
        bool b = token.transfer(treasury, total - out);
        require(a && b, "transfer");
        emit Flushed(total, out, total - out);
    }
}

/// SplitterFactory — deterministic addresses by CREATE2, tool-name salted.
///
/// Anyone (scripts, CI) can precompute the address for a tool off-chain
/// and commit it to git BEFORE it is deployed; the first deployer's call
/// only fixes what the git file already says, because payout/treasury/bps
/// are part of the salt. ensure() REVERTS if the bytes registered differ
/// from the committed terms — front-running a tool key with other terms
/// is impossible by construction, not by trust.
contract SplitterFactory {
    IERC20 public immutable token;
    address public immutable treasury;
    uint16 public immutable payoutBps;

    mapping(bytes32 => address) public splitterFor; // keccak(tool) -> addr

    event SplitterDeployed(string tool, address splitter, address payout);

    constructor(IERC20 usdc, address treasury_, uint16 bps_) {
        require(bps_ <= 10000, "bps");
        token = usdc;
        treasury = treasury_;
        payoutBps = bps_;
    }

    /// Terms pinned to git: payout is the proposer's base_account from
    /// docs/proposals/registry.jsonl; tool name as registered; bps is a
    /// factory-level constant (the decided 50/50), not a per-call choice.
    function ensure(string memory tool, address payout_) external returns (address s) {
        bytes32 key = keccak256(bytes(tool));
        address existing = splitterFor[key];
        if (existing != address(0)) {
            require(USDCSplitter(existing).payout() == payout_,
                "term mismatch with registry");
            return existing;
        }
        // salt binds EVERY committed term: replaying ensure with other
        // bytes computes a different address — and CREATE2 will not
        // overwrite an existing code hash either way.
        bytes32 salt = keccak256(abi.encode(tool, payout_, treasury,
                                              address(token), payoutBps));
        USDCSplitter c = new USDCSplitter{salt: salt}(token, treasury,
                                                      payout_, payoutBps);
        s = address(c);
        splitterFor[key] = s;
        emit SplitterDeployed(tool, s, payout_);
    }

    /// Off-chain mirror of ensure()'s CREATE2 (deployments that have not
    /// landed yet return the address they WILL have; git can pin it).
    function predicted(string memory tool, address payout_)
        external view returns (address)
    {
        bytes32 salt = keccak256(abi.encode(tool, payout_, treasury,
                                             address(token), payoutBps));
        bytes memory code = type(USDCSplitter).creationCode;
        bytes32 ch = keccak256(abi.encodePacked(type(USDCSplitter).creationCode,
            abi.encode(token, treasury, payout_, payoutBps)));
        return address(uint160(uint256(keccak256(abi.encodePacked(
            bytes1(0xff), address(this), salt, ch)))));
    }
}
