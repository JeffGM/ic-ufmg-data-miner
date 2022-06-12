import DataTransformer.DeveloperInformationAndAnalyticsJoiner
import DataTransformer.SourceCodeAnalyzer
import DataTransformer.SourceCodeStatisticsFilter

import DataExtractor.WorkanaDeveloperInformationProvider
import DataExtractor.GitHubSourceCodeProvider
import DataExtractor.InformationManager

import DataLoader.AnalyticsReaderAndUploader

def manage():
    informationManager = DataExtractor.InformationManager.InformationManager()
    informationManager.process()

    analyzer = DataTransformer.DeveloperInformationAndAnalyticsJoiner()
    analyzer.process()

    dataLoader = DataLoader.AnalyticsReaderAndUploader()
    dataLoader.process()











