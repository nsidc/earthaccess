# CLOUD COMPUTING TERMINOLOGY

This guide demystifies key cloud computing terms you'll need to know when working with NASA Earthdata, empowering you to harness the full potential of cloud-based Earth science workflows.

## In-region vs Out-of-region

**In-region**: In-region refers to compute resources running in the same cloud computing region as where the data is stored. NASA Earthdata is primarily hosted in the Amazon Web Services (AWS) `us-west-2` region. Accessing data directly in the cloud from the `us-west-2` Simple Storage Solution (S3) region is free to the user.

**Out-of-region**: When your compute resources are running locally, or in a different AWS region than where the data is stored. Data from NASA Earthdata's S3 buckets currently cannot be accessed from a different AWS region. In general, out-of-region access incurs egress charges and typically slower data transfer speeds.

## Cloud Optimized

Cloud-optimized refers to data, workflows, and computing approaches that are specifically designed or adapted to leverage cloud computing capabilities for efficient, scalable Earth science analysis.

Want to learn more? The team at Development Seed created an amazing [zine](https://zines.developmentseed.org/zines/cloud-native/#zine/1/) that transforms complex concepts into digestible, visual stories.
