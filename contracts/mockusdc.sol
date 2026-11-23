// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

/// Test-only USDC twin: same public shapes as Circle's USDC on Base
/// (EIP-3009 transferWithAuthorization settles USDC to a payTo without
/// any approve/transferFrom dance). Signatures are NOT checked here —
/// this file exists to prove the SPLITTER mechanics locally, and its
/// name says mock. Never deploy on a network that carries value.
contract MockUSDC {
    string public name = "USD Coin (mock for bench)";
    uint8 public constant decimals = 6;
    mapping(address => uint256) public balanceOf;

    function mint(address to, uint256 v) external { balanceOf[to] += v; }

    function transfer(address to, uint256 v) external returns (bool) {
        require(balanceOf[msg.sender] >= v, "ERC20: balance");
        balanceOf[msg.sender] -= v;
        balanceOf[to] += v;
        return true;
    }

    function transferWithAuthorization(
        address from, address to, uint256 value, uint256, uint256,
        bytes32, uint8, bytes32, bytes32) external returns (bool) {
        require(balanceOf[from] >= value, "authorization amount exceeds balance");
        balanceOf[from] -= value;
        balanceOf[to] += value;
        return true;
    }
}
