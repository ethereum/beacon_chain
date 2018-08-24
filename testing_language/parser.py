



def parser_raw(sentence):
    arrange_sentence, act_sentence, assert_sentence = sentence.split(':')
    print(parse_arrange(arrange_sentence))
    parse_act(act_sentence)
    print(parse_assert(assert_sentence))

def parse_arrange(sentence):
    tokens = sentence.split(',')
    config = { token[-1]:int(token[:-1]) for token in tokens}
    return config

def parse_act(sentence):
    tokens = sentence.split(',')
    for token in tokens:
        print(token)

def parse_assert(sentence):
    return list(sentence.strip())