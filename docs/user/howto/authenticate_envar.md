# How do I authenticate Earthdata Login using Environment Variables

## Problem

I want to store my Earthdata Login credentials as environment variables and use this strategy to authenticate using `earthaccess.login`.

## Solution

### 1. Create `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD` environment variables.

Instruction for creating environment variables on MacOS, Linux or Windows can be found in the [Authentication](https://earthaccess.readthedocs.io/en/stable/user/authenticate/#login-using-environment-variables) explanation section.

### 2. Login

```
import earthaccess

auth = earthaccess.login(strategy="environment")
```

## Discussion

This is a useful strategy if you are working on an untrusted machine or using a shared account.  `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD` environment variables can be created once at the beginning of your session.  Once you log out from the machine, the environment variables are deleted.

If you are working on a local machine, you can save environment variables in your profile (or similar startup file).  Instructions for doig this on MacOS, Linux and Windows can be found in the [Authenticate](https://earthaccess.readthedocs.io/en/stable/user/authenticate/#login-using-environment-variables) explanation section.