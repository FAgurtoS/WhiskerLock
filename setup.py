from setuptools import setup
setup(
    app=["pawpause.py"],
    name="Paw Pause",
    options={"py2app": {
        "iconfile": "PawPause.icns",
        "plist": {
            "CFBundleName": "Paw Pause",
            "CFBundleDisplayName": "Paw Pause",
            "CFBundleIdentifier": "local.felipe.pawpause",
            "CFBundleVersion": "1.0",
            "LSUIElement": True,
            "NSInputMonitoringUsageDescription":
                "Paw Pause watches keystroke patterns to detect when your cat is on the keyboard.",
        },
    }},
    setup_requires=["py2app"],
)
