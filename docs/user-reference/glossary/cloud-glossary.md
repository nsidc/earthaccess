# CLOUD COMPUTING TERMINOLOGY 

This guide demystifies key cloud computing terms you'll need to know when working with NASA Earthdata, empowering you to harness the full potential of cloud-based Earth science workflows.

## In-region vs Out-of-region

**In-region**: Accessing data directly in the cloud from the us-west-2 S3 region is free, where NASA's Earthdata is primarily hosted. This means your compute resources are in the same AWS region as the data.

**Out-of-region**: When your compute resources are in a different AWS region than where the data is stored, which incurs egress charges and typically slower data transfer speeds.

## Cloud Optimized 

Cloud-optimized refers to data, workflows, and computing approaches that are specifically designed or adapted to leverage cloud computing capabilities for efficient, scalable Earth science analysis.

Want to learn more? The team at Development Seed created an amazing [zine](https://zines.developmentseed.org/zines/cloud-native/#zine/23/) that transforms complex concepts into digestible, visual stories.