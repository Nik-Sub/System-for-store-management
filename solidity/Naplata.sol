pragma solidity ^0.8.2;

contract Naplata {
    address payable owner;
    address customer;
    address payable courier;

    uint amountToPay;
    uint complete;
    uint pickedUp;
    uint finished;

//    modifier notFinishedTrans () {
//        require ( finished == 0, "Finished." );
//        _;
//    }

    modifier transfer_complete () {
        require ( complete == 1, "Transfer not complete." );
        _;
    }

//    modifier insufficient_funds(uint amount){
//        require(amount / 10^17 <= customer.balance, "Insufficient funds.");
//        _;
//    }



    modifier transfer_not_completed(){
        require(complete == 0, "Transfer already complete.");
        _;
    }

    modifier picked_order(){
        require(pickedUp == 1, "Delivery not complete.");
        _;
    }

    modifier same_address(){
        require(msg.sender == customer, "Invalid customer account.");
        _;
    }

    constructor ( address cust, uint amount) {
        owner       = payable(msg.sender);
        customer       = cust;
        amountToPay = amount;
        complete = 0;
        pickedUp = 0;
        finished = 0;
    }

    function pickUpOrder ( address payable cour) external payable transfer_complete {
        courier = cour;
        pickedUp = 1;
    }

    function payCustomer () external payable transfer_not_completed {
        if (address(this).balance >= amountToPay){
            complete = 1;
        }
    }

    function transferMoneyToOwnerAndCourier ( ) external payable same_address transfer_complete picked_order {
        uint balance = address(this).balance;

        owner.transfer(80 * balance / 100);
        courier.transfer(20 * balance / 100);
    }



}