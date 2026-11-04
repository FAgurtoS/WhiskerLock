from setuptools import setup
setup(
    app=["whiskerlock.py"],
    name="WhiskerLock",
    options={"py2app": {
        "iconfile": "WhiskerLock.icns",
        "plist": {
            "CFBundleName": "WhiskerLock",
            "CFBundleDisplayName": "WhiskerLock",
            "CFBundleIdentifier": "local.felipe.whiskerlock",
            "CFBundleVersion": "1.0",
            "LSUIElement": True,
            "NSInputMonitoringUsageDescription":
                "WhiskerLock watches keystroke patterns to detect when your cat is on the keyboard.",
        },
    }},
    setup_requires=["py2app"],
)
