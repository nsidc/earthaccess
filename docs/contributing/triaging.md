## Introduction

Effective issue management is crucial for maintaining a streamlined development workflow. This document outlines the guidelines for issue labeling and management in GitHub, ensuring clarity, consistency, and efficiency. By clearly defining the roles of various labels and understanding how to link and use them, and distinguishing between discussions and issues, this guide aims to enhance the collaboration and productivity of our development team.

## Labeling Issues

Labeling issues effectively is crucial for maintaining clarity and organization within the project. Each label should provide clear information about the nature and status of an issue, making it easier to prioritize and address. Here’s a breakdown of how to label issues in GitHub and the purpose each label serves.

### Issue Types

- **bug**: Use for issues that identify bugs causing incorrect or unexpected behavior.

- **dependencies**: Use this label for issues concerning dependencies.

- **documentation**: Use this label for issues related to documentation.

- **library**: Use this label for issues related to core libraries or preparations for future plugin impacts.


### Requests and Feedback

- **enhancement**: Use this label for requests for new features or improvements to existing functionalities.

- **feedback**:  Use this label for issues where feedback is requested from the team or our community.

- **help**: Use this label for issues where additional help or contributions are needed.


### Special Labels

- **automation**: Use this label for issues related to the CI/CD pipeline or automation

- **duplicate**: Use this label for issues that are duplicates of existing ones.

- **good first issue** : Use this label to highlight issues good for newcomers who want to contribute to Earthaccess.

- **hackathon**: Use this label for issues to be discussed during hackdays.

- **wontfix**: Use this label for issues that won’t be addressed or fixed.


## Linking Labels in GitHub Markdown

When referencing a label in a GitHub issue or discussion, it is will be  useful to link to the label page to provide additional context and help others community members to quickly understand the issue's category.

### Syntax

To link to a label in GitHub Markdown, use the following syntax:

``` 
[label name](https://github.com/username/repository/labels/label-name)
```

### Example

For example, to link to the "hackathon" label in the nsidc/earthaccess repository, you would use the following syntax:


``` 
[hackathon](https://github.com/nsidc/earthaccess/labels/hackathon)
```

!!! tip
    When linking to labels, it is a good practice to use the label name as the link text, as shown in the example above. This makes it clear to others what label is being referenced, and helps to avoid confusion.

## Close Issue as Not Planned

This section will cover the guidelines for when to use the "Close Issue as Not Planned" label, and how to handle issues that are not planned or feasible.

### Overview

The "Close Issue as Not Planned" label is used to indicate that an issue is not planned or feasible to be addressed.

### When to Use This Label

Use the "Close Issue as Not Planned" label when:

- An issue is not aligned with the project's goals or priorities
- An issue is not feasible to be addressed due to technical or resource constraints
- An issue is a duplicate of an existing issue that has already been addressed

!!! tip
    When closing an issue as not planned, keep the following best practices in mind:

    * Provide a clear explanation as to why the issue is not planned or feasible
    * Offer alternative solutions or workarounds, if possible
    * Link to relevant documentation or resources, if applicable

### Discussions vs Issues    

This section would cover the guidelines for when to use discussions versus issues, and how to migrate between them.

### Overview
Discussions and issues are two different features in GitHub that serve distinct purposes.

### Discussions

Discussions are used for:

- Brainstorming and idea generation.
- Feature requests and feedback.
- General questions and topics.

### Issues

Issues are used for:

- Reporting bugs and errors.
- Tracking progress on specific tasks or projects.
- Requesting changes or improvements.


#### When to Migrate 

**Migrate a discussion to an issue when:**

* Specific task or project is identified.
* A* bug or error is reported.
* A change or improvement is requested.

**Migrate an issue to a discussion when:**

* The issue is a feature request or idea
* The issue is a general question or topic
* The issue is not specific or actionable




