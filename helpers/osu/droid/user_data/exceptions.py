class MissingRequiredArgument(Exception):

    def __init__(self, missed_arg_name: str):
        self.missed_arg = missed_arg_name

        super().__init__(self.missed_arg)

    def __str__(self):
        return f'Missing required argument for this command: {self.missed_arg} needs to be {True}'
