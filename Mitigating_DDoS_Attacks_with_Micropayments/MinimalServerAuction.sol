contract MinimalServerAuction {

    event Deposit(
        address from,
        uint deposit, 
        uint bid, 
        uint256 pubKey
    );

    struct Bidder {
        uint balance;
        uint bid;
        uint256 pubKey;
    }

    address internal sellerAddress;
    mapping(address => Bidder) private Bidders;

    constructor(address _sellerAddress) public {
        sellerAddress = _sellerAddress;
        if (sellerAddress == 0)
          sellerAddress = msg.sender;
    }

    function newBidder(uint deposit, uint bid, uint256 pubKey) public {
        ...
        emit Deposit(msg.sender, deposit, bid, pubKey)
    }

    function deductFromBalance(address customer, uint price) private {
        require(msg.sender == sellerAddress);
        ...
    }
}
