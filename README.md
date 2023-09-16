# iepProjekat
System for store management | Python, Solidity 2023
• System is separeted in 3 web services, for owner, customer and courier.
• Every service has its own .dockerfile. They are all connected via one .yaml file which is running on Docker platform.
• Owner has functions to configure store, customer can buy stuff, and courier can delivery them.
• Payment is executing via Ethereum Blockchain platform.
• Python and Blockchain are connected via .sol file which is commanly called Contract. There is also regulated order of
actions ( e.g. customer pay for order, courier must make delivery and after that owner will get money, and courier his
part).
