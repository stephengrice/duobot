#!/usr/bin/env python

objs = [
    {
        "english":"hi",
        "arabic":"ahlan"
    }
]
brain = {}
for i in objs:
    brain[i["english"]] = i["arabic"]
    brain[i["arabic"]] = i["english"]

print(i)
print(brain["hi"])
print(brain["ahlan"])
