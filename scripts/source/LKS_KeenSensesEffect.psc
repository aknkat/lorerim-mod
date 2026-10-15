Scriptname LKS_KeenSensesEffect extends ActiveMagicEffect
; This effect itself is the 60-second, engine-persisted cooldown.
; NoRecast and the spell-entry conditions prevent refresh/duplicate starts.
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
