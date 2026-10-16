Scriptname LKS_KeenSensesController extends Quest
; A saved deadline is checked only on activation. No update timer is required.
; Game.GetRealHoursPassed is vanilla; do not save a per-session real-time clock.

Spell Property DetectionSpell Auto
Race Property KhajiitRace Auto
Race Property KhajiitVampireRace Auto

; Retained for compatibility with v0.1.3 saves and pending legacy callbacks.
; This variable no longer gates activation.
Bool coolingDown = False
Float readyAtHours = 0.0

Bool Function TryActivate(Actor akTarget, Actor akCaster)
    ; Clear an obsolete v0.1.3 lock; it has no recoverable deadline.
    If coolingDown
        coolingDown = False
    EndIf
    Actor playerRef = Game.GetPlayer()
    If akTarget != playerRef || akCaster != playerRef
        Return False
    EndIf
    Race currentRace = playerRef.GetRace()
    If currentRace != KhajiitRace && currentRace != KhajiitVampireRace
        Return False
    EndIf
    Spell pulse = DetectionSpell
    If pulse == None
        Return False
    EndIf

    ; Read shared state AFTER the last native call. A reentrant request may
    ; have accepted an activation during GetPlayer/GetRace/GetRealHoursPassed.
    Float nowHours = Game.GetRealHoursPassed()
    Float remainingHours = readyAtHours - nowHours
    ; More than 63 seconds cannot be a normal remaining cooldown. Rebase once
    ; if the native clock rolls backward; do not leave an unreachable deadline.
    If remainingHours > 0.0175
        readyAtHours = nowHours + (1.0 / 60.0)
        Return False
    EndIf
    If remainingHours > 0.0
        Return False
    EndIf
    ; Commit before the next external call; rejected input never extends it.
    readyAtHours = nowHours + (1.0 / 60.0)
    pulse.Cast(playerRef, playerRef)
    Return True
EndFunction

Event OnUpdate()
    ; A pending v0.1.3 update may still arrive. It cannot clear readyAtHours.
    coolingDown = False
EndEvent
