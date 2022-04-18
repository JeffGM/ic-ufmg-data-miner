#importar dados pessoais
import pandas
import csv
import json

scraped_profiles = pandas.read_json("scraped_profiles.json")

#importar dados das habilidades
github_data = pandas.read_csv("final_report_curated.csv")

relationship_data = pandas.read_csv("habilities_and_extensions_relationship.csv", header=None)

print("aaaa")

relationship_data = relationship_data.set_index(0).to_dict()[1]
#buscar perfil nas habilidades e corresponder com dados pessoais

profiles_stats = dict()
counter = 0
for scraped_profile in scraped_profiles.iterrows():
    profile_key = scraped_profile[1]['githubURL']
    profiles_stats[profile_key] = dict()

    for i in range(0, len(scraped_profile[1]['skills']['Habilidades'])):
        skill = scraped_profile[1]['skills']['Habilidades'][str(i)]
        profiles_stats[profile_key][skill] = 0

        for github_stat in github_data.iterrows():
            if github_stat[1]['username'] in scraped_profile[1]['githubURL']:
                if skill in relationship_data and github_stat[1]['path'] == relationship_data[skill]:
                    profiles_stats[profile_key][skill] = github_stat[1]['loc']
                    break
    counter += 1

    if counter == 25:
        break

output_file = open("profiles_stats.json", "w")
json.dump(profiles_stats, output_file)
output_file.close()



#corresponder habilidades listadas com dados do github