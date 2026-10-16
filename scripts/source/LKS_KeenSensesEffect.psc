Scriptname LKS_KeenSensesEffect extends ActiveMagicEffect
; This effect itself is the 60-second, engine-persisted cooldown.
; NoRecast prevents duplicate applications. Spell-entry conditions only check
; the player and race; never condition this effect on its own absence.
; The separate native Detect Life spell lasts only two seconds.

Spell Property DetectionSpell Auto
Race Property KhajiitRace Auto
Race Property KhajiitVampireRace Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
    Actor playerRef = Game.GetPlayer()
    If akTarget != playerRef || akCaster != playerRef
        Return
    EndIf

    Race currentRace = playerRef.GetRace()
    If currentRace != KhajiitRace && currentRace != KhajiitVampireRace
        Return
    EndIf

    If DetectionSpell != None
        DetectionSpell.Cast(playerRef, playerRef)
    EndIf
EndEvent
