from brownie import config, network, interface
from scripts.helpful_scripts import get_account, FORKED_LOCAL_ENVIRONMENTS
from scripts.get_weth import get_weth
from web3 import Web3

#amount:0.1
amount = Web3.toWei(0.1, "ether")

def main():
    account = get_account();
    erc20_address = config["networks"][network.show_active()]["weth_token"]
    if network.show_active() in FORKED_LOCAL_ENVIRONMENTS:
        get_weth()
    lending_pool = get_lending_pool()
    # approve sending out ERC-20 tokens
    approve_erc20(amount, lending_pool.address, erc20_address, account)
    print("Depositing...")
    # Referral code is deprecated hence we passed 0
    txn = lending_pool.deposit(erc20_address,amount,account.address,0, {"from":account})
    txn.wait(1)
    print("Deposited!!")
    borrowable_eth, total_debt = get_borrowable_data(lending_pool, account)
    # borrow DAI
    print("Borrowing dai")
    # dai in terms of eth
    dai_eth_price = get_asset_price(config["networks"][network.show_active()]["dai_eth_price_feed"])
    # converting borrowable ETH to borrowable DAI and multiplying by 95%
    amount_dai_to_borrow = (1 / float(dai_eth_price)) * (borrowable_eth * 0.95)
    print(f"We are going to borrow {amount_dai_to_borrow} DAI")
    # NOW WE BORROW
    dai_address = config["networks"][network.show_active()]["dai_token"]
    borrow_txn = lending_pool.borrow(dai_address, Web3.toWei(amount_dai_to_borrow, "ether"),
    1, 0, account.address, {"from":account})
    borrow_txn.wait(1)
    print("We borrowed some DAI")
    get_borrowable_data(lending_pool, account)
    # repay all
    repay_all(amount, lending_pool, account)
    print("You just deposited, borrowed and repayed with aava, brownie, chainlink")

def repay_all(amount, lending_pool, account):

    approve_erc20(
        Web3.toWei(amount, "ether"),
         lending_pool,
        config["networks"][network.show_active()]["dai_token"],
         account
        )
     
    repay_txn = lending_pool.repay(config["networks"][network.show_active()]["dai_token"], 
    amount, 1, account.address, {"from": account}
    )
    repay_txn.wait(1)
    print("Repayed!!!")

def get_asset_price(dai_eth_price_feed):
    dai_eth_contract_feed = interface.AggregatorV3Interface(dai_eth_price_feed)
    #returns a single value from the tuple at the index
    latest_price = dai_eth_contract_feed.latestRoundData()[1]
    converted_price = Web3.fromWei(latest_price, "ether")
    print(f"DAI/ETH price is {converted_price}")
    return converted_price


def get_borrowable_data(lending_pool, account):
    (
      totalCollateralETH,
      totalDebtETH,
      availableBorrowsETH,
      currentLiquidationThreshold,
      ltv,
      healthFactor
    ) = lending_pool.getUserAccountData(account.address);
    availableBorrowsETH = Web3.fromWei(availableBorrowsETH, "ether")
    totalCollateralETH = Web3.fromWei(totalCollateralETH, "ether")
    totalDebtETH = Web3.fromWei(totalDebtETH, "ether")
    print(f"{totalCollateralETH} worth of ETH deposited")
    print(f"you can borrow {availableBorrowsETH} worth of ETH")
    print(f"{totalDebtETH} worth of ETH borrowed")
    return (float(availableBorrowsETH), float(totalDebtETH))

def get_lending_pool():
    # interact with lending_pool_addresses providers interface to fetch lending pool contracts address
    address = config["networks"][network.show_active()]["lending_pool_addresses_provider"]
    lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
        address
    )

    lending_pool_address = lending_pool_addresses_provider.getLendingPool()
    # now interact with lending pool
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool


def approve_erc20(amount, spender, erc20_address, account):
    print("Approving ERC20...")
    erc20 = interface.IERC20(erc20_address)
    txn = erc20.approve(spender, amount, {"from":account})
    txn.wait(1)
    print("Approved!!")
    return txn

