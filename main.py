import requests
from stellar_base import Horizon
from stellar_sdk.asset import Asset
from stellar_sdk.keypair import Keypair
from stellar_sdk.network import Network
from stellar_sdk.server import Server
from stellar_sdk.transaction_builder import TransactionBuilder

# 거래원장 생성코드 (후에 안쓰임)
def data_handler(response):
    print(response)

def get_ledger_data():
    # Horizon객체 생성
    ledger_data = Horizon(horizon_uri="https://horizon.stellar.org")
    # 원장에 요청 보냄
    ledger_data = ledger_data.ledgers(cursor='now', order='asc', sse=True)
    # ledger_data 응답
    data_handler(ledger_data)

# 지갑 생성 코드 후에 계정은 새로 짜야함
def make_stellar_wallet():
    pair = Keypair.random()
    print(f"비밀키(절대비밀): {pair.secret}")
    print(f"공개키(공개가능): {pair.public_key}")
    return pair.secret, pair.public_key

# 지갑 생성 이후 계정을 만드는 코드 (지갑에 XLM이 들어가야 계정생성 되는건데 여기선 10000xlm을 공짜로 줌
# 계정 생성때 얻은 공개키를 매개변수로 받음
def register_my_wallet(pub_key):
    public_key = pub_key
    response = requests.get(f"https://friendbot.stellar.org?addr={public_key}")
    if response.status_code ==200:
        print(f"성공! 10000루멘 입금 완료\n{response.text}")
    else:
        print(f"실패! 또 돈주기 버튼 누르면 안댐.\n{response.text}")

# 잔액 확인코드 native=xlm 이고 credit_alphanum4가 KWC 임.
def Check_Account_Balance(pubkey):
    server = Server("https://horizon-testnet.stellar.org")
    account = server.accounts().account_id(pubkey).call()
    for balance in account['balances']:
        print(f"자산 종류: {balance['asset_type']}, 잔액: {balance['balance']}")


# 스텔라 기반으로 KWC 코인 만드는 코드
# 발행자 계정을 만들어서 다른 계정으로 쏴줄거임. 그니까 여기선 내 고유 계정을 만들어서 써야겠지.
# 트러스트 라인 만드는것도 여기 포함.
def make_KWC_TrustLine(Distributor_SecretKey):
    server = Server(horizon_url ="https://horizon-testnet.stellar.org")
    network_passphrase = Network.TESTNET_NETWORK_PASSPHRASE

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
                                            base_fee=10000,)
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
                                              base_fee=10000,)
                           .append_payment_op(destination = distributor_public,
                                              amount = "1",
                                              asset_code = asset_KWC.code,
                                              asset_issuer = asset_KWC.issuer,
                                              )
                           .build()
                           )

    payment_transaction.sign(issuing_keypair)
    payment_transaction_resp = server.submit_transaction(payment_transaction)
    print(f"KWC를 배포용 계정에게 전달 완료: \n{payment_transaction_resp}")

def my_Transaction(sender_secret_key, receiver_pubkey, amount):
    sender_keypair = Keypair.from_secret(sender_secret_key)
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
                   .add_text_memo("첫번째 거래")
                   .append_payment_op(destination=receiver_pubkey,
                                      amount=amount,
                                      asset_code="KWC",
                                      asset_issuer="GA3BGOVKSWXDDHWEULDLFMCS52E5GGCHIJ4HQD2THG3ZNBKHCEO2U2CQ"
                                      )
                   .set_timeout(30)
                   .build()
                   )
    transaction.sign(sender_keypair)
    print(transaction.to_xdr())
    print("----------------------------------------------------")
    response = server.submit_transaction(transaction)
    print(response)

#Issuing_secretkey,Issuing_pubkey = make_stellar_wallet()
#Distributor_secretkey, Distributor_pubkey = make_stellar_wallet()

# 분배용 계정 (내계정)
Issuing_secretkey = "SBSMECGTTJ2OHMQN26YB7WRXCZUVEILD4YU4GC3XC7XKNIGVGRPMFRPY"
Issuing_pubkey = "GA3BGOVKSWXDDHWEULDLFMCS52E5GGCHIJ4HQD2THG3ZNBKHCEO2U2CQ"
# 배포용 계정 (이것도 내계정)
Distributor_secretkey = "SDGFWWNGFEIWHO7B4UFJ5CATRAAQQBWPRGIFQM54A5XLQZLQEX7ELWUP"
Distributor_pubkey = "GBDEH7A3URBVX7AEQE62H25X3XPFBPHHUPPOW66FXJZW4AMDEQNZIPMS"
# 거래 테스트옹 (네 계정)
Receiver_secretkey = "SAMS4IEO3DWMIZYJDT7A3PKYHR6CMRKVOWISBKJI42HYV4BDSIQYQIJN"
Receiver_pubkey = "GDDV5KSO6K7J4DRGHTUBVL7OKIZZTK7I64VHTA45U5S6UJMS4UMVQITE"

'''한번만 하면됨 10000xlm 받는거
register_my_wallet(Issuing_pubkey)
register_my_wallet(Distributor_pubkey)
register_my_wallet(Receiver_pubkey)

Check_Account_Balance(Issuing_pubkey)
Check_Account_Balance(Distributor_pubkey)
Check_Account_Balance(Receiver_pubkey)
'''

# KWC 생성하서 보냈음. 100000 KWC 생성 됐음!! 아래 코드 한번만 실행하면 됨.
#make_KWC_TrustLine(Issuing_secretkey, Receiver_secretkey)

'''
# 이제 거래를 해봅니다
my_Transaction(sender_secret_key=Receiver_secretkey,
               receiver_pubkey=Distributor_pubkey,
               amount="1000")
'''
#register_my_wallet("GCUCHFSPMMIAVJEB2SZ724TQHJNGGSQZUV7AX7Z35TEWL3ZPMTMPUDI7")
#make_KWC_TrustLine("SB34IPTNV7FDDXN67QPXAIPSOD3CPEN2PUXQH5UOHTFOV5C7MJ3YKQH2")
Check_Account_Balance("GCUCHFSPMMIAVJEB2SZ724TQHJNGGSQZUV7AX7Z35TEWL3ZPMTMPUDI7")
#pub = "GC7HFZSXL7DFFGBOQM7UXOSHYZKV2GBW4OOEMDXXC5GX4KUVQ6RVVUXV"
#sec = "SDKUTEDZJCXLK2AOJBD6IM3VYUCTX5ENVV5F3WMF7V7MYNJINCITYAZ7"
#make_KWC_TrustLine("SDKUTEDZJCXLK2AOJBD6IM3VYUCTX5ENVV5F3WMF7V7MYNJINCITYAZ7")