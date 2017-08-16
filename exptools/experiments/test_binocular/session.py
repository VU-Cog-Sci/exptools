from exptools.core import Session

class BinocularSession(Session):


    def __init__(self, *args, **kwargs):
        self.create_screen()
        super(BinocularSession, self).__init__(*args, **kwargs)

    def run(self):
        """docstring for fname"""
        # cycle through trials
        self.close()
