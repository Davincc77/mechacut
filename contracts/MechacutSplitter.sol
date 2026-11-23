// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

/// @title MechacutSplitter
/// @notice A dumb, fixed-ratio USDC splitter. One x402 payment carries
///         exactly ONE payTo (EIP-3009 has one `to` field) — so the split
///         is not in the wire protocol, it is BEHIND it: point payTo at
///         this contract and the money divides on-chain, verifiable by
///         anyone from the settlement tx alone.
///
///         Design rules (mechacut bundle95, doctrine 2026-11-24):
///         - No owner. No admin. No pause. No upgrade. Recipients and
///           ratio are set once, at deploy, and never change.
///         - Pull-only. Circle's FiatToken credits a contract with no
///           receive hook (the facilitator pays gas, the payer stays
///           gasless), so nothing can reenter on arrival.
///         - `distribute()` is permissionless: EITHER payee — or anyone
///           at all — can flush the balance. Funds can never be held
///           hostage by one side; there is nothing to hostage.
///         - Rounding: payeeA is floor(total * bpsA / 10000); payeeB
///           receives the exact remainder. Sum(toA, toB) == total always.
///         - If either transfer fails, the whole call reverts: the split
///           is all-or-nothing, never half-delivered.
contract MechacutSplitter {
    /// @notice the USDC (FiatToken) this splitter is allowed to move
    address public immutable usdc;
    address public immutable payeeA;
    address public immutable payeeB;
    /// @notice basis points (1/100 of a percent) of every distribution
    ///         that goes to payeeA; payeeB gets the remainder.
    uint256 public immutable bpsA;

    event Distributed(address indexed caller, uint256 total, uint256 toA, uint256 toB);

    error ZeroToken();
    error ZeroPayee();
    error SamePayees();
    error BadBps();

    constructor(address usdc_, address payeeA_, address payeeB_, uint256 bpsA_) {
        if (usdc_ == address(0)) revert ZeroToken();
        if (payeeA_ == address(0) || payeeB_ == address(0)) revert ZeroPayee();
        if (payeeA_ == payeeB_) revert SamePayees();
        if (bpsA_ < 1 || bpsA_ > 9999) revert BadBps();
        usdc = usdc_;
        payeeA = payeeA_;
        payeeB = payeeB_;
        bpsA = bpsA_;
    }

    /// @notice Pure preview of the split math for a given gross amount.
    ///         Deterministic: callers can compute their payout offline.
    function splitOf(uint256 total) public view returns (uint256 toA, uint256 toB) {
        toA = (total * bpsA) / 10000;
        toB = total - toA;
    }

    /// @notice Flush the entire USDC balance to the two payees at the
    ///         deploy-time ratio. Anyone may call; only the payees can
    ///         receive. No-op (returns zeros) when the balance is zero.
    function distribute() external returns (uint256 total, uint256 toA, uint256 toB) {
        total = _balanceOf(address(this));
        if (total == 0) return (0, 0, 0);
        (toA, toB) = splitOf(total);
        _send(payeeA, toA);
        _send(payeeB, toB);
        emit Distributed(msg.sender, total, toA, toB);
    }

    function _balanceOf(address who) internal view returns (uint256 bal) {
        (bool ok, bytes memory data) = usdc.staticcall(
            abi.encodeWithSignature("balanceOf(address)", who)
        );
        if (!ok || data.length < 32) revert BadTokenReturn();
        bal = abi.decode(data, (uint256));
    }

    error BadTokenReturn();

    function _send(address to, uint256 amount) internal {
        (bool ok, bytes memory data) = usdc.call(
            abi.encodeWithSignature("transfer(address,uint256)", to, amount)
        );
        // ERC-20s that return nothing are not USDC; accepted anyway for
        // the empty-data case, explicitly true otherwise.
        require(ok && (data.length == 0 || abi.decode(data, (bool))), "usdc transfer failed");
    }
}
