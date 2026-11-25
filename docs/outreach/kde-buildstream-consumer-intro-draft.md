# Draft: introduction of Tromsø to the KDE BuildStream maintainers

Status: draft for the owner. No agent sends this message. The owner decides
if, where and when to send it.

Plan: [UPSTREAM-ALIGNMENT.md](../UPSTREAM-ALIGNMENT.md), section 6.
Issue: [tuna-os/tromso#521](https://github.com/tuna-os/tromso/issues/521).

Possible places: an issue on `packaging/kde-buildstream`, or the Matrix room
of KDE Linux.

## Message

Subject: A downstream consumer of kde-buildstream (Tromsø, bootc image)

Hello Harald, hello Aleix,

I maintain Tromsø (<https://github.com/tuna-os/tromso>). It is a community
image of KDE Plasma on freedesktop-sdk. BuildStream builds it, and the result
is a bootc image with composefs. It is not a KDE project.

Tromsø has its own elements for Qt, Frameworks and Plasma today. I want to
replace them with a junction to `packaging/kde-buildstream`. The plan is in
the Tromsø repository. Three questions:

1. Do you plan tags or a stable branch for `kde-buildstream`? Tromsø pins a
   commit now. A tag for each known-good state would make updates safer.
2. Tromsø overrides the nested `freedesktop-sdk.bst` junction, because the
   image needs bootc and a different systemd configuration. Is that a use
   that you want to keep possible? `kde-buildstream!14` looks related.
3. When `kde-buildstream!68` merges, do the generated `kde/` elements stay
   on Git `master`, or do you plan a release line?

Tromsø can give things back:

- elements that Tromsø has and `kde-buildstream` does not have;
- patches that make some Plasma dependencies optional;
- reports from a second consumer with a different image model.

I do not ask for support. I ask only for the answers above, if you have
them.

Thank you for the work on this.

## Notes for the owner

- All facts in the message come from clones made on 2026-11-25.
- The questions do not ask the upstream to change its plan.
- Send the message before step 10 of the plan. Steps 1 to 9 do not need an
  answer.
