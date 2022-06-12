import GitHubSourceCodeProvider
import WorkanaDeveloperInformationProvider

class InformationManager():
    def __init__(self):
        pass

    def process(self):
        gitProvider = GitHubSourceCodeProvider.GitHubSourceCodeProvider()
        developerProvider = WorkanaDeveloperInformationProvider.WorkanaDeveloperInformationProvider()

        developerProvider.process()
        gitProvider.process()