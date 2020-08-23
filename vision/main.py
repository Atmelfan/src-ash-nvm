import time

from common.common_csci import Csci


class TestCsci(Csci):

    def __init__(self) -> None:
        super().__init__(name='test')

    def run(self):
        super().run()
        self.logger.info("tick")


if __name__ == '__main__':
    test = TestCsci()
    test.start()
