# How do I authenticate with NASA Earthdata Login interactively

## Problem

I would like to authenticate my NASA Earthdata Login account using `earthaccess`

## Solution

```
>>> import earthaccess

>>> auth = earthaccess.login()
Enter your Earthdata Login username: <your_username>
Enter your Earthdata password: <your_password>
```

## Discussion

If you have not configured your system to store Earthdata Login credentials, calling
`earthaccess.login()` prompts you for you username and password.

If you need to force `earthaccess` to prompt you for your credentials use:

```
>>> auth = earthaccess.login(strategy="interactive")
```

Assigning the result of `earthaccess.login()` to a variable is not required but doing so
allows you to access session information.