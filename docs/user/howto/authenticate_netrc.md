# How do I authenticate with Earthdata Login using a `.netrc`

## Problem

I would like to authenticate my NASA Earthdata Login account with `earthaccess` using a `.netrc`

## Solution

### 1. Create a `.netrc` file

If you already have a `.netrc` file, you can add your Earthdata Login credentials to this file following the instructions on the [Login using a `.netrc`](https://earthaccess.readthedocs.io/en/stable/user/authenticate/#login-using-a-netrc).  These instructions can also be used to create a new `.netrc` file.

Alternatively, you can use `earthaccess.login(persist=True)`.

```
>>> import earthaccess

>>> auth = earthaccess.login(persist=True)
Enter your Earthdata Login username: <your_earthdata_username>
Enter your Earthdata password: <your_earthdata_password>
```

This will create a `.netrc` and authenticate your credentials in one step.

Once a `.netrc` has been created, you do not have to repeat this step.

### 2. Login

If you created your .netrc manually or you already have a `.netrc` file.

```
>>> auth = earthaccess.login(strategy="netrc")
```

`strategy="netrc"` is not required but is useful if you want to be explicit.  You can also use

```
>>> auth = earthaccess.login()
```

## Discussion

!!! Do not use this strategy on untrusted machines or with shared accounts

earthaccess does not currently support encrypted .netrc files. This strategy of writing credentials in plain text to disk should not be used on untrusted machines or shared user accounts.

