import opencontracts
from bs4 import BeautifulSoup
import email
import quopri
import json

with opencontracts.enclave_backend() as enclave:

  enclave.print("Fiat Swap started running in the Enclave!")

  seller = enclave.user_input("Please enter the PayPal handle of the seller:")
  amount = int(enclave.user_input("Please enter the transaction price in cents (as integer):"))
  message = enclave.user_input("Please enter the message the seller wants you to use in the transaction:").strip()
  secret = enclave.user_input("Please enter the secret generated by the seller:")

  offerID = enclave.keccak(seller, amount, message, secret, types=('string', 'uint256', 'string', 'string'))
  warning = f"""
  The information you entered would produce the offerID:
  {'0x' + offerID.hex()}
  Before proceeding to make a payment:
     - call ethOffered() to verify you will receive enough ETH
     - call secondsLeft() to verify you have enough time to claim your payout.
  """
  enclave.print(warning)

  instructions = f"""
  1) Pay ${amount/100} to {seller} and use the message '{message}'.
  2) Navigate to the 'Recent Activity' section on the home page and select your transaction
  3) Click the 'Submit' button on the right.
  """


  def parser(mhtml):
    mht_string = quopri.decodestring(mhtml.replace("=\n", "")).decode('latin-1')
    mhtml = email.message_from_string(mht_string)
    html = [_ for _ in mhtml.walk() if _.get_content_type() == "text/html"][0]
    parsed = BeautifulSoup(html.get_payload(decode=False))
    txn_details = json.loads(parsed.findAll("div", {"id": 'js_transactionDetailsView'})[0]['data-details'])
    txn_seller = txn_details['p2pRedirect']['repeatTxn']['email']
    assert txn_seller == seller, f"Saved wrong transaction, seller was not {seller}"
    total_amount = parsed.findAll("div", {"class": 'transactionNetAmount'})[0]
    payment_sign = total_amount.find_all("span", {"class": 'accessAid'})[0].text.strip()
    assert payment_sign == "negative", f"Payment was wrong sign ({payment_sign} instead of 'negative')"
    total_amount = total_amount.find("span", {"class": 'accessAid'}).nextSibling.strip().lstrip('$')
    message = parsed.findAll("dd", {"class": 'smallGray'})[0].text.strip()
    total_amount = int(float(total_amount)*100)
    assert total_amount >= amount, f"Found PayPal transaction labeled '{message}', adding up to ${total_amount/100} which is too low."
    return total_amount

  enclave.open_up_domain("paypal.com")
  payment = enclave.interactive_session(url='https://paypal.com', parser=parser, instructions=instructions)
  enclave.print(f'Your total payment of ${payment/100} to {seller} was confirmed.')
  enclave.submit(offerID, types=("bytes32",), function_name="paypalPurchase")
