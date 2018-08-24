import re


class TestCase:
    def __init__(self, sentence):
        arrange_sentence, act_sentence, assert_sentence = sentence.split(':')
        self.configs = {token[-1]: int(token[:-1])
                        for token in arrange_sentence.split(',')}
        self.actions = [token.strip() for token in act_sentence.split(',')]
        self.assertions = list(assert_sentence.strip())

    def arrange_test(self):
        raise NotImplementedError

    def act_test(self):
        raise NotImplementedError

    def assert_test(self):
        raise NotImplementedError

    def run(self):
        self.arrange_test()
        self.act_test()
        self.assert_test()


class TextInterpreter(TestCase):
    def arrange_test(self):
        print("\nArrangments:\n")
        print(f"First validator set: {self.configs['V']} validators")
        print(f"EPOCH_LENGTH: {self.configs['E']}")
        print(f"SHARD_COUNT: {self.configs['S']}")
        print(f"MIN_COMMITTEE_SIZE: {self.configs['M']}")

    def act_test(self):
        self.slot = 1
        print("\nActions:\n")
        for action in self.actions:
            print(f"Slot {self.slot}: ")
            self.handle_action(action)
            self.slot += 1

    def handle_action(self, action):
        if action == "":
            print("\tDo nothing in this round")
        else:
            for token in action.split(" "):
                print("\t", end="")
                self.handle_action_token(token)

    def handle_action_token(self, token):
        if token.endswith(']'):
            print(f"Assert: current slot {self.slot} should be {token[2:-1]}")
        else:
            regex = r'(?:\[([0-9]*)\])?([0-9]*)-([0-9]*)([A-Z\*])([A-Z\*])'
            _slot, v_from, v_to, b_parent, b_vote = re.match(
                regex, token).groups()
            slot = self.slot if _slot is None else _slot
            print(f"Validators {v_from}-{v_to} of the validator set of slot {slot}"
                  f" vote on {b_vote}, a child of {b_parent}")

    def assert_test(self):
        print("\nAssertions:\n")
        head, justified, finalized = self.assertions
        print(f"Assert head is at {head}")
        print(f"Assert last justified block is {justified}")
        print(f"Assert last finalized block is {finalized}")
