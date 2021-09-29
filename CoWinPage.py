import requests
from flask import Flask, render_template, request
from stellar_sdk import Server, Network, Asset, TransactionBuilder
from stellar_sdk.keypair import Keypair


app = Flask(__name__)

@app.route('/')
def e2():
    return render_template('e2.html')

@app.route('/genkey', methods=['POST'])
def make_stellar_wallet():
    pair = Keypair.random()
    request.form['value1']
    value1 = pair.secret
    request.form['value2']
    value2 = pair.public_key

    return render_template('e2.html',value1=value1, value2=value2)

@app.route('/balance', methods=['POST'])
def Check_Account_Balance():
    myPub = request.form['myPub']
    request.form['myMoney']
    server = Server("https://horizon-testnet.stellar.org")
    account = server.accounts().account_id(myPub).call()

    balance = account['balances'][0]
    myMoney = balance['balance']

    return render_template('e2.html',myMoney = myMoney)

@app.route('/Purchase', methods=["POST"])
def Purchase():
    receiver_pubkey = request.form['pur_Pub']
    amount = request.form['pur_Fee']
    sender_keypair = Keypair.from_secret("SB34IPTNV7FDDXN67QPXAIPSOD3CPEN2PUXQH5UOHTFOV5C7MJ3YKQH2")
    sender_pubkey = sender_keypair.public_key

    # 서버
    server = Server(horizon_url="https://horizon-testnet.stellar.org")

    # 거래용 계정 생성 매 거래마다 바뀔거야 시퀀스넘버랑 주소가 들어가니까.
    sender_account =server.load_account(sender_pubkey)

    # 트랜잭션
    base_fee = server.fetch_base_fee()
    network_passphrase = Network.TESTNET_NETWORK_PASSPHRASE
    asset_KWC = Asset("KWC", "GA3BGOVKSWXDDHWEULDLFMCS52E5GGCHIJ4HQD2THG3ZNBKHCEO2U2CQ")

    transaction = (TransactionBuilder(source_account=sender_account,
                                      network_passphrase=network_passphrase,
                                      base_fee=base_fee,)
                   .append_payment_op(destination=receiver_pubkey,
                                      amount=amount,
                                      asset_code="KWC",
                                      asset_issuer="GA3BGOVKSWXDDHWEULDLFMCS52E5GGCHIJ4HQD2THG3ZNBKHCEO2U2CQ"
                                      )
                   .set_timeout(30)
                   .build()
                   )
    transaction.sign(sender_keypair)
    server.submit_transaction(transaction)

    return render_template('e2.html')

@app.route('/Sale', methods=["POST"])
def Sale():
    sender_secretkey = request.form['sale_Sec']
    amount = request.form['sale_KWC']
    sender_keypair = Keypair.from_secret(sender_secretkey)
    sender_pubkey = sender_keypair.public_key

    # 서버
    server = Server(horizon_url="https://horizon-testnet.stellar.org")

    # 거래용 계정 생성 매 거래마다 바뀔거야 시퀀스넘버랑 주소가 들어가니까.
    sender_account =server.load_account(sender_pubkey)

    # 트랜잭션
    base_fee = server.fetch_base_fee()
    network_passphrase = Network.TESTNET_NETWORK_PASSPHRASE
    asset_KWC = Asset("KWC", "GA3BGOVKSWXDDHWEULDLFMCS52E5GGCHIJ4HQD2THG3ZNBKHCEO2U2CQ")

    transaction = (TransactionBuilder(source_account=sender_account,
                                      network_passphrase=network_passphrase,
                                      base_fee=base_fee,)
                   .append_payment_op(destination="GCUCHFSPMMIAVJEB2SZ724TQHJNGGSQZUV7AX7Z35TEWL3ZPMTMPUDI7",
                                      amount=amount,
                                      asset_code="KWC",
                                      asset_issuer="GA3BGOVKSWXDDHWEULDLFMCS52E5GGCHIJ4HQD2THG3ZNBKHCEO2U2CQ"
                                      )
                   .set_timeout(30)
                   .build()
                   )
    transaction.sign(sender_keypair)
    server.submit_transaction(transaction)

    return render_template('e2.html')

@app.route('/genregister', methods = ["POST"])
def genregister():
    public_key = request.form['gen_pub']
    requests.get(f"https://friendbot.stellar.org?addr={public_key}")

    return render_template('e2.html')

@app.route('/trustline', methods=["POST"])
def trustline():
    server = Server(horizon_url="https://horizon-testnet.stellar.org")
    network_passphrase = Network.TESTNET_NETWORK_PASSPHRASE
    Distributor_SecretKey = request.form['trust_sec']
    issuing_keypair = Keypair.from_secret("SBSMECGTTJ2OHMQN26YB7WRXCZUVEILD4YU4GC3XC7XKNIGVGRPMFRPY")
    issuing_public = issuing_keypair.public_key
    distributor_keypair = Keypair.from_secret(Distributor_SecretKey)
    distributor_public = distributor_keypair.public_key

    # tx는 Sequence 넘버가 필요하다. 송신계정(발행계정) 에서 Horizon 요청 해 얻어와야함
    distributor_account = server.load_account(distributor_public)
    # 새로운 화폐단위 생성
    asset_KWC = Asset("KWC", issuing_public)

    # TrustLine 생성하기. 발행계정에서 발행한 코인을 믿을 수 있다는걸 보증
    trust_transaction = (TransactionBuilder(source_account=distributor_account,
                                            network_passphrase=network_passphrase,
                                            base_fee=10000, )
                         .append_change_trust_op(asset_code=asset_KWC.code,
                                                 asset_issuer=asset_KWC.issuer,
                                                 limit="1000000000")
                         .set_timeout(100)
                         .build()
                         )

    trust_transaction.sign(distributor_keypair)
    trust_transaction_resp = server.submit_transaction(trust_transaction)
    print(f"트러스트 라인 새로 구축했음: \n{trust_transaction_resp}")

    # 생성용 계정이 배포용 계정에게 코인 전달하기
    issuing_account = server.load_account(issuing_public)
    payment_transaction = (TransactionBuilder(source_account=issuing_account,
                                              network_passphrase=network_passphrase,
                                              base_fee=10000, )
                           .append_payment_op(destination=distributor_public,
                                              amount="1",
                                              asset_code=asset_KWC.code,
                                              asset_issuer=asset_KWC.issuer,
                                              )
                           .build()
                           )

    payment_transaction.sign(issuing_keypair)
    server.submit_transaction(payment_transaction)

    return render_template('e2.html')

if __name__ == "__main__":
    app.run()

'''배포자 아이디
#pubkey = "GCUCHFSPMMIAVJEB2SZ724TQHJNGGSQZUV7AX7Z35TEWL3ZPMTMPUDI7"
#seckey = "SB34IPTNV7FDDXN67QPXAIPSOD3CPEN2PUXQH5UOHTFOV5C7MJ3YKQH2"
'''
#async 검색