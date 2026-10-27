using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# Flight Attendant Tycoon - MUSIQUE ON / OFF.
# Le joueur interagit avec le bouton : la musique se coupe POUR LUI SEUL. Il re-clique : elle revient.
# Les autres joueurs ne sont pas touches.
#
# Dans UEFN :
#   - "Lecteur audio" (Audio Player) avec ta musique : Lecture automatique NON, En boucle OUI,
#     Peut etre entendu par : Joueurs enregistres, pas de spatialisation ;
#   - un "Bouton" (Button) sur ton icone ;
#   - pose ce device et remplis Musique et Bouton.

musique_device := class(creative_device):
    @editable Musique : audio_player_device = audio_player_device{}
    @editable Bouton : button_device = button_device{}

    var Coupes : [player]logic = map{}
    var Vus : [player]logic = map{}

    OnBegin<override>()<suspends>:void =
        Bouton.InteractedWithEvent.Subscribe(Basculer)
        # chaque joueur qui arrive entend la musique
        loop:
            for (P : GetPlayspace().GetPlayers(), not Vus[P]):
                if (set Vus[P] = true) {}
                Musique.Register(P)
                Musique.Play(P)
            Sleep(1.0)

    Basculer(Agent:agent):void =
        if (P := player[Agent]):
            if (Coupes[P]?):
                if (set Coupes[P] = false) {}
                Musique.Register(P)
                Musique.Play(P)
            else:
                if (set Coupes[P] = true) {}
                Musique.Stop(P)
                Musique.Unregister(P)
