from github2pandas.utility import Utility
from github2pandas.version import Version
from pathlib import Path
import os
from tabulate import tabulate
import pandas as pd
import matplotlib.pyplot as plt

github_token = os.environ['TOKEN']
git_repo_name = os.environ['CI_REPOSITORY_NAME']
git_repo_owner = os.environ['CI_REPOSITORY_OWNER']
    
default_data_folder = Path("data", git_repo_name)

imagefilename = "AddedlinesOfCode.png"
readmefilename = "README.md"

def replaceTextBetween(originalText, delimeterA, delimterB, replacementText):
    leadingText = originalText.split(delimeterA)[0]
    trailingText = originalText.split(delimterB)[1]
    return leadingText + delimeterA + replacementText + delimterB + trailingText

def getDataToPlot(df, author):
    data = df.copy()
    data = data[data.author==author]
    data['day'] = pd.to_datetime(data['commited_at'])
    data.set_index('day', inplace=True)
    result = data.groupby(pd.Grouper(freq='D')).sum()
    result['lines_sum'] = result.total_added_lines.cumsum().astype('int64')
    return result

if __name__ == "__main__":
    print(git_repo_owner, git_repo_name)
    repo = Utility.get_repo(git_repo_owner, git_repo_name, github_token, default_data_folder)
    Version.clone_repository(repo=repo, data_root_dir=default_data_folder, github_token=github_token)
    Version.no_of_proceses = 8
    Version.generate_version_pandas_tables(repo = repo, data_root_dir=default_data_folder)
    
    users = Utility.get_users(default_data_folder)
    print(users)
    pdCommits = Version.get_version(data_root_dir=default_data_folder)
    pdEdits = Version.get_version(data_root_dir=default_data_folder, filename=Version.VERSION_EDITS)

    print(pdCommits.author.unique())
    pdEdits = pdEdits.merge(pdCommits[['commit_sha', 'author', 'commited_at']], left_on='commit_sha', right_on='commit_sha')
    pdEdits = pdEdits.merge(users[['anonym_uuid', 'login']], left_on='author', right_on='anonym_uuid')
    
    # Generate Table 
    pdFileEdits = pdEdits.groupby(['commit_sha']).first()
    counts = pdFileEdits.groupby(['login']).agg({'total_added_lines': 'sum', 'total_removed_lines': 'sum'})
    print(counts.to_markdown())
    with open(readmefilename, 'r') as filehandle:
        filecontent = filehandle.read()
    newfilecontent = replaceTextBetween(filecontent, "## Text and Tables", "## Diagrams",
                                        '\n' + counts.to_markdown() + '\n')
    with open(readmefilename, 'w') as filehandle:
        filehandle.write(newfilecontent)
    print(newfilecontent)
    
    # Generate Figure 
    fig, ax = plt.subplots()
    for index, user in users.iterrows():
        print(user)
        df = getDataToPlot(pdFileEdits, user.anonym_uuid)
        print(df)
        if len(df.lines_sum):
            if len(df.lines_sum) == 1:
                df.reset_index().plot.scatter(x = 'day', y = 'lines_sum', label = user.login, ax = ax, zorder=10)
            else:
                df.lines_sum.plot(drawstyle="steps-mid", label = user.login, linewidth = 1, ax = ax)

    ax.legend(bbox_to_anchor=(0.5, 1.05))
    ax.set_xlabel("Date")
    ax.set_ylabel('Added Lines of Code')
    print(type(pdFileEdits.commited_at.min()))
    print(pdFileEdits.commited_at.max()+ pd.Timedelta("1 days"))
    print((pdFileEdits.commited_at.max()+ pd.Timedelta("1 days")))
    ax.set_xlim(pdFileEdits.commited_at.min(), 
                (pdFileEdits.commited_at.max()+ pd.Timedelta("1 days")))
    plt.tight_layout()
    fig.savefig(imagefilename)
