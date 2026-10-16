Scriptname LKS_KeenSensesController extends Quest
; One persistent instance owns the lock and the single native update timer.
; Recasting/replacing/expiring a trigger effect cannot replace this instance.

Spell Property DetectionSpell Auto
Race Property KhajiitRace Auto
Race Property KhajiitVampireRace Auto

Bool coolingDown = False

Bool Function TryActivate(Actor akTarget, Actor akCaster)
    If coolingDown
        Return False
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

    ; Recheck after native/property calls, then acquire the shared lock before
    ; the next external call. Reentrant requests must not re-register a timer.
    If coolingDown
        Return False
    EndIf
    coolingDown = True
    RegisterForSingleUpdate(60.0)
    pulse.Cast(playerRef, playerRef)
    Return True
EndFunction

Event OnUpdate()
    ; The sole accepted activation scheduled this event. No polling/restarts.
    coolingDown = False
EndEvent
