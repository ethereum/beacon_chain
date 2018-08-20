# eth2.0 Beacon Chain
[![CircleCI](https://circleci.com/gh/ethereum/beacon_chain.svg?style=svg)](https://circleci.com/gh/ethereum/beacon_chain)
> Implements a proof of concept beacon chain for a sharded pos ethereum 2.0. Spec in progress can be found [here](https://notes.ethereum.org/SCIg8AH5SA-O4C1G1LYZHQ?view).

## Installation
Using a python3 environment, run the following to install required libraries:
```
make build
```

## Deploy
```
make deploy
```

NOTE: We suggest using virtualenv to sandbox your setup.

## Tests
```
pytest tests
```

Run with `-s` option for detailed log output
