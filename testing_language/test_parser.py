from parser import parser_raw


def test_parser():
    test_case = "100V,8E,32S,8M: 0-5*A, 0-5AB, 2-7AC [2]6-7AC, 0-4CD,, [=6] 0-4DE 5-7AB: E**"
    parser_raw(test_case)


if __name__ == '__main__':
    test_parser()