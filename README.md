# Fiat Swap

### TL;DR

This contract allows token sellers to put their tokens into a contract, which only releases the tokens to someone who can prove that they appropriately paid the seller on some traditional digital payment service (such as Venmo, MPesa, Zelle, CashApp, PayPal...) that takes care of handling the fiat payments, as well as KYC and AML compliance. The goal is to allow anyone to freely swap between local currency inside a verified fiat account, and tokens on the blockchain. 

This is a key building block needed to provide financial products (such as insurance, loans or savings accounts) to anyone in the world via the blockchain: anyone who receives capital from a smart contract could use it to do things in the fiat-world, and anyone who wants to deposit capital into smart contracts could do so - as long they use the same payment service as some individual who's willing to swap between crypto and fiat, even if the two don't trust each other.

Here are some exciting ways anyone could improve the contract, and start a business around it: Add more fiat payment services. Design a market which efficiently matches buyers with sellers, maybe by finding a way to create the role of liquidity providers as in [Uniswap](https://uniswap.com/) for example. Integrate with [OpenGSN](https://opengsn.org/) to allow the token-buyer to start without any ETH in their wallet, enabling a trustless fiat-crypto onramp (directly onto L2!). 

### The big picture
There's a lot of spare capital parked on Ethereum. People decided to put it there because they have high hopes for the potential of the technology, and now they would love to put it to productive (and interest-earning) use. For now, there are only few "productive" use-cases for capital in the blockchain world: align the incentives of consensus participants via proof-of-stake, or provide liquidity that allows users to swap tokens, for example. But if we're honest, there's almost no way right now in which this capital could be put to productive use in the _real world_, i.e. to solve problems that have existed before blockchains came around. The consequence: people mostly use their capital to speculate on the prices of NTFs, ERC20s and other tokens. We think this falls fundamentally short of what blockchain capital - which is globally available and has perfect contractual security built-in - _could_ be used for: rent it out or provide insurance to individuals who are inadequately served by existing financial and legal institutions, such as small business owners in low income countries, for example.

But we're missing some key pieces to realize this vision: Ethereum transactions must become cheaper without reducing the trustworthiness of the system (shout out to [Arbitrum](https://offchainlabs.com/), [Optimism](https://www.optimism.io/), [ZKSync](https://zksync.io/) and [Polygon](https://polygon.technology/) for working on this!). For loans, we need to empower people to prove to a contract that they have a clean credit history (which becomes possible with our [Proof-Of-ID](https://app.opencontracts.io/#/open-contracts/proof-of-id) idea for example, but also shoutout to the [Proof-Of-Humanity](https://www.proofofhumanity.id/) project!). For insurance, people need to able to prove they actually had a damage (check out our [Weather-Insurance](https://app.opencontracts.io/#/open-contracts/weather-insurance) contract for an example of this!).  And finally, we need to make crypto capital easily convertible to and from local fiat-currencry, wherever you are, because most of the world still runs on it. And that's what this contract is about!

### How it works

Before offering any tokens for sale, the seller first computes a unique `offerID` as follows (e.g. via the `offerID` contract function):
```
offerID = hash(sellerHandle, priceInCent, transactionMessage, paymentService, buyerSellerSecret)
```
`paymentService` specifies the online payment website (currently it must be the string `"Venmo"`, but eventually `"MPesa"` or `"CashApp"` should be supported as well). `sellerHandle` is the name of the seller's account on the payment website (currently their Venmo handle). `priceInCent` is an integer specifying how much the buyer has to pay to the seller. `transactionMessage` is a string specifying what message the buyer has to use for their payment. `buyerSellerSecret` is a large, random number generated by the seller.

The `hash` function always produces the same `offerID` from the same inputs, but you cannot compute the inputs from a given `offerID` in any other way than randomly trying out all plausible inputs until you find the exact set of inputs that procudes a given `offerID`. This means that as long as `buyerSellerSecret` is a large, random number known only to the buyer and seller, even someone who correctly guesses the `sellerHandle`,`priceInCent`,`transactionMessage` and `paymentService` couldn't figure out thany public `offerID` was produced from those inputs. 

To make an offer to a buyer, the seller calls the `offerTokens` function to deposit their tokens into the contract, and specifies their `offerID`, the Ethereum address of the buyer, and the number of seconds the buyer has to claim the offer without fearing that it could be retracted or fulfilled by someone else. Then, they would share the offer inputs (`sellerHandle` , `priceInCent`, `transactionMessage`, `paymentService` and `buyerSellerSecret`) with the buyer, who can compute the corresponding `offerID` and check (via the `weiOffered` function) that they would receive enough tokens for making the transaction. If that is the case, they can make the specified payment, and then call the `buyTokens` function. This will start an oracle enclave, which first receives the offer inputs from the buyer and computes the `offerID`. Next, it opens up the website of the payment service in an interactive session, where the user passes 2FA and captchas and shows the enclave that they made the transaction specified by the inputs. If everything checks out, the enclave signs the offerID along with the user's Ethereum address such that the user can submit them to the contract, which then releases the tokens to the user. If the user doesn't fulfill their end of the deal in time, the seller can call `retractOffer` to get their tokens back from the contract.
