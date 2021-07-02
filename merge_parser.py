"""
merge_parser

UseCase-
1.While working on any merge request use the specified template & Label [~ Development Team]
2.Use merged MR to create a commit for Changelog update and release objects [~ this script]

Usage:
    merge_parser.py --authkey=<authkey> --project-path=<project> --component_project-path=<project> [--url=<url>]\
                    --tag_for_release=<tag_for_release>\
                    --target_branch_for_MR=<target_branch_for_MR> --mr_state=<mr_state>\
                    --type_of_action=<type_of_action> --scheduled_after=<scheduled_after>\
                    --scheduled_before=<scheduled_before>

Options:
    --authkey=<authkey>                           Access token for authentication with GitLab.
    --project-path=<project>                      Path to GitLab project in the form <namespace>/<project>
    --component_project-path=<project>            Path to ATPCU GitLab project.(Used for parsing compatible component info)----IGNORE(Can be removed)
    --url=<url>                                   Gitlab host URL. [default: https://gitlab.com/]
    --tag_for_release=<tag_for_release>           Specify which tags to be used for release
    --target_branch_for_MR=<target_branch_for_MR> Specify the target branch for MR in the project as well as for SS
    --mr_state=<mr_state>                         Specify the state of MR's in the project(merged ,opened , closed)
    --type_of_action=<type_of_action>             Specify the type of action (ChangeLog or Release)
    --scheduled_after=<scheduled_after>           Time in Date-ISO 8601 format for collecting all the MR's updated after.
    --scheduled_before=<scheduled_before>         Time in Date-ISO 8601 format for collecting all the MR's updated before.
    --help -h                                     Show this screen

"""

import sys
from datetime import date
import json
import gitlab
from urllib3 import disable_warnings
from docopt import docopt
from datetime import datetime, timedelta
from dateutil.parser import parse
from links_templates import HEADER, ARTIFACT_LINKS, RELEASE_LINKS, TAGS_LINKS\
    , COPYRIGHT ,DEPENDENCIES_VERSION_LINKS

disable_warnings()  # this is needed to avoid warnings

FINAL_SUMMARY = " "  # HEADER + ADDED + DEPRECATED + REMOVED + CHANGED + REFACTORED
CHANGE_LOG_SUMMARY = ""  # Considering only one instance runs for each MR

# Prepare the type of issues resolved in a release
ADDED = "\n### ADDED\n"
ADDED_CR = 0  # to validate that there are feature request being ADDED
DEPRECATED = "\n### DEPRECATED\n"
DEPRECATED_CR = 0
REMOVED = "\n### REMOVED \n"
REMOVED_CR = 0
CHANGED = "\n### CHANGED \n"
CHANGED_CR = 0
REFACTORED = "\n### REFACTORED \n"
REFACTORED_CR = 0

def summary(merge_sum):
    """
    split & extract the required info from the merge request description
    """

    try:
        temp = merge_sum.split("# Merge Request DoD Checklist", 1)
        release_des = temp[0].split("# Change Synopsis", 1)
        # print(release_des[1])
        global CHANGE_LOG_SUMMARY
        temp = release_des[1].split("Summary for the changes introduced:", 1)
        temp = temp[1].split("# Merge Request DoD Checklist", 1)
        CHANGE_LOG_SUMMARY = temp[0]
        # print(CHANGE_LOG_SUMMARY)
    except:
        release_des.append("n/a")
        release_des[1] = ":x: ERROR: Use of incorrect template"
    return release_des[1]



def description_parser(title_to_parse, merge_to_parse, labels_in_mr):
    """
    Parse MR based on it's description section to prepare release info
    """
    # Deduce the type of merge request
    # typeList = "feature|deprecate|remove|defect|refactor"
    # x = re.findall(typeList, title_to_parse, re.IGNORECASE)
    global ADDED, ADDED_CR, DEPRECATED, DEPRECATED_CR, REMOVED, REMOVED_CR,\
           CHANGED, CHANGED_CR, REFACTORED, REFACTORED_CR
    print("--------- Deducing type of MR")
    if not labels_in_mr:
        labels_in_mr.append('feature')

    for label in labels_in_mr:
        if label == 'feature':
            print("It's a feature addition request")
            ADDED = ADDED + "\n" + "<details close>\n\
            <summary><b> " + title_to_parse + "</b></summary>\n\
            <br>\n" + summary(merge_to_parse) + "</details>\n"
            ADDED_CR += 1
        elif label == 'deprecate':
            print("It's a temproray fix request")
            DEPRECATED = DEPRECATED + "\n" + "<details close>\n\
            <summary><b> " + title_to_parse + "</b></summary>\n\
            <br>\n" + summary(merge_to_parse) + "</details>\n"
            DEPRECATED_CR += 1
        elif label == 'remove':
            print("It's a feature removal request")
            REMOVED = REMOVED + "\n" + "<details close>\n\
            <summary><b> " + title_to_parse + "</b></summary>\n\
            <br>\n" + summary(merge_to_parse) + "</details>\n"
            REMOVED_CR += 1
        elif label == 'defect':
            print("It's a defect resolution request")
            CHANGED = CHANGED + "\n" + "<details close>\n\
            <summary><b> " + title_to_parse + "</b></summary>\n\
            <br>\n" + summary(merge_to_parse) + "</details>\n"
            CHANGED_CR += 1
        elif label == 'refactor':
            print("It's a code refactoring request")
            REFACTORED = REFACTORED + "\n" + "<details close>\n\
            <summary><b> " + title_to_parse + "</b></summary>\n\
            <br>\n" + summary(merge_to_parse) + "</details>\n"
            REFACTORED_CR += 1
        else:
            print(
                "--------- Not a valid label--THIS MR will be considered as a feature for this release. "
            )
            ADDED = ADDED + "\n" + "<details close>\n\
            <summary><b> " + title_to_parse + "</b></summary>\n\
            <br>\n" + summary(merge_to_parse) + "</details>\n"
            ADDED_CR += 1


class GitlabRelease:
    """
    GitLab class for maintaining all MR related actions
    """
    def __init__(self, url, authkey, project, project_component, tag_for_release,
                 target_branch_for_MR, mr_state, type_of_action, scheduled_after,scheduled_before):
        # Parse command line arguments
        self.url = url
        self.authkey = authkey
        self.project_name = project
        self.project = None
        self.mrs = None  # list of all merge requests
        # Create python-gitlab server instance
        server = gitlab.Gitlab(self.url,
                               self.authkey,
                               api_version=4,
                               ssl_verify=False)
        # Get an instance of the project and store it off
        self.project = server.projects.get(self.project_name)
        self.project_comp = server.projects.get(project_component)
        self.tags = tag_for_release
        self.target_branch = target_branch_for_MR
        self.mr_state = mr_state
        self.type_of_action = type_of_action
        self.scheduled_after = scheduled_after
        self.scheduled_before = scheduled_before

    def process_mrs(self):
        """
        Get the list of all MR within the specified arguments make function calls based on actions
        """
        # Get all MRs in the project
        # https://docs.gitlab.com/ee/api/merge_requests.html#list-merge-requests
        #MR_Commit_at = datetime.strptime(self.scheduled_before,'%Y-%m-%d') - timedelta(days = 90)
        Updated_after_ls = parse(self.scheduled_before) - timedelta(days = 90)
        # print(Updated_after_ls)
        # All MR's in last 90 days.
        mrs = self.project.mergerequests.list(all=True,
                                              state=self.mr_state,
                                              updated_after=Updated_after_ls,
                                              updated_before=self.scheduled_before,
                                              target_branch=self.target_branch)
        # print(mrs)
        print("--------- All new merged MR in project : %s since %s " % (self.project_name, self.scheduled_after))
        count_mr = 0
        for merge_req in mrs:
            # If the MR is merged in the specified window
            if (merge_req.merged_at <= self.scheduled_before)and(merge_req.merged_at >= self.scheduled_after):
                print("\n--------- Merge Request ID: %d, Title: %s" % (merge_req.iid, merge_req.title))
                print(merge_req.merged_at)
                # print(type(merge_req.labels))
                print('    Labels: ' + ','.join(merge_req.labels))
                # print('    Number of notes in discussion: ' + str(len(merge_req.notes.list())))
                # print(merge_req.description)
                count_mr += 1
                description_parser(merge_req.title, merge_req.description, merge_req.labels)
                # Update ChangeLog for every MR merged withing the specified schedule
                if self.type_of_action == "ChangeLog":
                    print("--------- Updating ChangeLog.md")
                    self.update_changelog(self.tags, merge_req)
        if self.type_of_action == "Release":
            self.create_release(self.tags, count_mr)

    def create_release(self, tag_rel, num_ncr):
        """
        Create and update the release
        """
        # Create release by taking into account the new merge summary and tags eg: 'v5.0.102.4'
        # https://python-gitlab.readthedocs.io/en/stable/gl_objects/projects.html?highlight=release#id24
        print("\n\n--------- Total number to MR's processed: %s" % (num_ncr))
        num_ncr = "\n<br> <mark><b>  Number of MR's : " + str(
            num_ncr) + "</b></mark><br>"
        global FINAL_SUMMARY, ADDED, DEPRECATED, REMOVED, CHANGED, REFACTORED
        # Remove extra sub-headings
        if ADDED_CR == 0:
            ADDED = ''
        if DEPRECATED_CR == 0:
            DEPRECATED = ''
        if REMOVED_CR == 0:
            REMOVED = ''
        if CHANGED_CR == 0:
            CHANGED = ''
        if REFACTORED_CR == 0:
            REFACTORED = ''

        FINAL_SUMMARY = HEADER + str(
            num_ncr) + ADDED + DEPRECATED + REMOVED + CHANGED + REFACTORED
        release_info = str(tag_rel) + "  [" + str(
            date.today()) + "]"
        artifacts_link = ARTIFACT_LINKS + tag_rel
        atpcu_links = DEPENDENCIES_VERSION_LINKS + tag_rel + "/versions_config.json"
        # Update header with compatible atpcu version info
        print("--------- Parsing versions_config.json for updating applicable SS")
        self.update_atpcu_version()
        # create new release for project
        print("--------- Creating release with tag %s" %(tag_rel))
        '''
        self.project.releases.create({
            'name': release_info,
            'tag_name': tag_rel,
            'description': FINAL_SUMMARY,
            "assets": {
                "links": [{
                    "name": "Artifactory Binaries",
                    "url": artifacts_link,
                    "link_type": "other"
                },
                {
                   "name": "ATPCU Compatible Version",
                    "url": atpcu_links,
                    "link_type": "other"
                }]
            }
        })'''
        # release = self.project.releases.list()
        print("--------- Release Created" )

    def update_changelog(self, tag_rel, merge_req):
        """
        Update the ChangeLog with the merged MR
        """
        # Update the change log for ETCS core code
        commit_msg = "Update ChangeLog.md for " + merge_req.title
        # find the id for the blob (ChangeLog.md)
        print("--------- Finding current ChangeLog.md ")
        cl_id = [
            d['id'] for d in self.project.repository_tree(ref=merge_req.target_branch)
            if d['name'] == 'ChangeLog.md'
        ][0]
        # get the content
        file_content = self.project.repository_raw_blob(cl_id)
        file_content = file_content.decode("utf-8")
        file_content_str = str(file_content)
        file_content_str = file_content_str.split(
            '`All notable changes to this project will be documented here.`',
            1)
        file_content_str = file_content_str[1]
        # insert applicable links [](url) -- Created before exists
        links = "[Project Release]("+ RELEASE_LINKS + tag_rel + ")"
        links = links + "\n\n[Project Tag](" + TAGS_LINKS + tag_rel + ")"

        # prepare new data for commit
        file_update = COPYRIGHT + merge_req.title + " [" + str(
            date.today()
        ) + "] \n\n" + CHANGE_LOG_SUMMARY + "\n\n" + links + "\n\n" + file_content_str
        target_branch = merge_req.target_branch
        commit_data = {
            'branch':
            target_branch,
            'commit_message':
            commit_msg,
            'actions': [{
                'action': 'update',
                'file_path': 'ChangeLog.md',
                'content': file_update,
            }]
        }
        self.project.commits.create(commit_data)
        print("--------- Updated ChangeLog.md for %s" %(merge_req.title))

 # Specific to a project, remove or adapt as per yours 
    def update_atpcu_version(self):
        """
        Update the release obj with the compatible ATPCU version info
        """
        global FINAL_SUMMARY
        # find the id for the blob (versions_config.json)
        cl_id = [
            d['id'] for d in self.project_comp.repository_tree(ref=self.target_branch)
            if d['name'] == 'versions_config.json'
        ][0]
        # get the content
        file_content_atpcu_json = self.project_comp.repository_raw_blob(cl_id)
        file_content_atpcu_json = file_content_atpcu_json.decode("utf-8")
        file_content_atpcu_json = str(file_content_atpcu_json)
        #print(file_content_atpcu_json)
        atpcu_version = '''
        \n
# Component Dependencies


<details close>
<summary><b>Click to see compatible components :arrow_down_small: </b></summary>
<br>

| Component | Version |
| ------ | ------ |
'''
        # list_location = list()
        # list_target_path = list()
        list_component = list()
        list_version = list()

        loaded_json = json.loads(file_content_atpcu_json)
        # print (loaded_json)
        for compo in loaded_json:
            list_component.append(compo["component"])
            list_version.append(compo["version"])
            # try:
            #     list_location.append(compo["git_path"])
            # except KeyError:
            #     list_location.append(compo["artifactory_path"])
            # list_target_path.append(compo["target_path"])
        # print(list_location)
        # print(list_target_path)
        # print(list_component)
        # print(list_version)

        for i in range(len(list_component)):
            # print(i)
            if i == 0:
                atpcu_version = atpcu_version + '| ' + list_component[
                    i] + ' | ' + list_version[i] + ' |'
            else:
                atpcu_version = atpcu_version + '\n' + '| ' + list_component[
                    i] + ' | ' + list_version[i] + ' |'

        # print(atpcu_version)
        temp = FINAL_SUMMARY.split('<br>',1 )   # NOTE : THe first <br> for split. DO Not delete from template.
        temp[0] = temp[0] + atpcu_version + "<br><br> \n </details>"
        FINAL_SUMMARY = temp[0]+temp[1]
        print("--------- FINAL release summary prepared")
        # print (FINAL_SUMMARY)

    def run(self):
        """
        runner for the class GitlabRelease
        """
        self.process_mrs()

if __name__ == '__main__':
    ARGUMENTS = docopt(__doc__)
    print (ARGUMENTS)
    sys.exit(
        GitlabRelease(ARGUMENTS['--url'], ARGUMENTS['--authkey'],
                      ARGUMENTS['--project-path'],
                      ARGUMENTS['--component_project-path'],
                      ARGUMENTS['--tag_for_release'],
                      ARGUMENTS['--target_branch_for_MR'],
                      ARGUMENTS['--mr_state'], ARGUMENTS['--type_of_action'],
                      ARGUMENTS['--scheduled_after'],ARGUMENTS['--scheduled_before']).run())
