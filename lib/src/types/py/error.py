class BtcError(Exception):
    pass


class InvalidTransaction(BtcError):
    pass


class InvalidBlock(BtcError):
    pass


class InvalidBlockHeader(BtcError):
    pass


class InvalidTransactionInput(BtcError):
    pass


class InvalidTransactionOutput(BtcError):
    pass


class InvalidMerkleRoot(BtcError):
    pass


class InvalidHash(BtcError):
    pass


class InvalidSignature(BtcError):
    pass


class InvalidPublicKey(BtcError):
    pass


class InvalidPrivateKey(BtcError):
    pass
