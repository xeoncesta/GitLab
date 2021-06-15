# GitLab_Automation
Automatically create releases in GitLab and update the ChangeLog.md as well.

UseCase-
1.While working on any merge request use the specified template & Label [~ Development Team]
2.Use merged MR to create a commit for Changelog update and release objects [~ this script]

Usage:
    `merge_parser.py --authkey=<authkey> --project-path=<project> --component_project-path=<project> [--url=<url>]\
                    --tag_for_release=<tag_for_release>\
                    --target_branch_for_MR=<target_branch_for_MR> --mr_state=<mr_state>\
                    --type_of_action=<type_of_action> --scheduled_after=<scheduled_after>\
                    --scheduled_before=<scheduled_before>`

Options:
-    --authkey=<authkey>                           Access token for authentication with GitLab.
-    --project-path=<project>                      Path to GitLab project in the form <namespace>/<project>
-    --component_project-path=<project>            Path to ATPCU GitLab project.(Used for parsing compatible component info)----IGNORE(Can be removed)
-    --url=<url>                                   Gitlab host URL. [default: https://gitlab.com/]
-    --tag_for_release=<tag_for_release>           Specify which tags to be used for release
-    --target_branch_for_MR=<target_branch_for_MR> Specify the target branch for MR in the project as well as for SS
-    --mr_state=<mr_state>                         Specify the state of MR's in the project(merged ,opened , closed)
-    --type_of_action=<type_of_action>             Specify the type of action (ChangeLog or Release)
-    --scheduled_after=<scheduled_after>           Time in Date-ISO 8601 format for collecting all the MR's updated after.
-    --scheduled_before=<scheduled_before>         Time in Date-ISO 8601 format for collecting all the MR's updated before.
-    --help -h                                     Show this screen
    
    Can be adapted as per your project needs and structure. See links_templates.py for modifying the final assets/links.
