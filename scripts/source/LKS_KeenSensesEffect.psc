Scriptname LKS_KeenSensesEffect extends ActiveMagicEffect
; Short activation trigger only. Cooldown state belongs to the quest controller.
; Retain the three legacy properties so old saved instances can finish safely.

Spell Property DetectionSpell Auto
Race Property KhajiitRace Auto
Race Property KhajiitVampireRace Auto
Quest Property CooldownController Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
    Actor playerRef = Game.GetPlayer()
    If akTarget != playerRef || akCaster != playerRef
        Return
    EndIf

    If CooldownController == None
        Return
    EndIf
    If !CooldownController.IsRunning()
        If !CooldownController.Start()
            Return
        EndIf
    EndIf
    LKS_KeenSensesController controller = CooldownController as LKS_KeenSensesController
    If controller != None
        controller.TryActivate(akTarget, akCaster)
    EndIf
EndEvent
