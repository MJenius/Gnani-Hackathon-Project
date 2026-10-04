import itertools
import tempfile
import os
import unittest
from unittest.mock import patch
from app.agent.planner.slots import signature_slots
from app.agent.planner.evon import MockEvon
from app.agent.planner.contract import planning_input
from app.mission.execution import persistent

LANGUAGES = [
    ['Tell Ananya', 'ask if four thirty works', 'find some parking near her office',
     "get fuel if it does not add more than 5 minutes"],
    ['Ananya ko bata do', '04:30 pucho', 'office ke paas parking dhoondo',
     'fuel agar five minutes se zyada detour na ho'],
    ['ಅನನ್ಯ ಅವರಿಗೆ ಹೇಳಿ', 'ನಾಲ್ಕೂವರೆ ಗಂಟೆಗೆ ಆಗುತ್ತದೆಯೇ ಕೇಳಿ', 'ಅವರ ಕಚೇರಿ ಹತ್ತಿರ ಪಾರ್ಕಿಂಗ್ ಹುಡುಕಿ',
     'ಐದು ನಿಮಿಷಕ್ಕಿಂತ ಹೆಚ್ಚು ಆಗದಿದ್ದರೆ ಇಂಧನ ತುಂಬಿಸಿ'],
]

class SlotTests(unittest.TestCase):
    def test_reordering_variants_preserve_frozen_plan(self):
        expected = MockEvon().plan_mission(planning_input(', '.join(LANGUAGES[0])))
        for clauses in LANGUAGES:
            for order in itertools.permutations(clauses):
                text = 'Okay, um please ' + '; '.join(order) + '!'
                with self.subTest(text=text):
                    self.assertEqual(signature_slots(text), {'contact':'Ananya','meeting_time':'16:30',
                                     'parking':'near office','fuel':True,'max_detour':5})
                    self.assertEqual(MockEvon().plan_mission(planning_input(text)), expected)
        variants = [
            'ಅನನ್ಯಾ ಅವರಿಗೆ ತಿಳಿಸಿ; ನಾಲ್ಕು ಮೂವತ್ತಕ್ಕೆ ಆಗುತ್ತಾ ಕೇಳಿ; ಆಫೀಸ್ ಬಳಿ parking ನೋಡಿ; 5 ನಿಮಿಷಗಳಿಗಿಂತ ಹೆಚ್ಚು ತಡವಾಗದಿದ್ದರೆ ಪೆಟ್ರೋಲ್ ಹಾಕಿಸಿ',
            'Ananya ko bata dena, four thirty poocho, office ke pass parking dhundho, fuel tabhi agar 5 min se jyada detour nahi ho',
            'notify Ananya and ask whether 16:30 is okay and look for parking near the office and add fuel only if it adds at most five minutes',
        ]
        for text in variants:
            with self.subTest(text=text):
                self.assertEqual(MockEvon().plan_mission(planning_input(text)), expected)

    def test_changed_missing_ambiguous_negated_or_extra_instructions_fail_closed(self):
        mutations = [
            [('Ananya','Anita'), ('four thirty','five thirty'), ('5 minutes','10 minutes'),
             ('Tell Ananya','do not Tell Ananya'), ('get fuel','do not get fuel'),
             ('near her office','near home'), (' near her office',''),
             ('Tell Ananya','tell Ananya or Anita')],
            [('Ananya','Anita'), ('04:30','04:45'), ('five minutes','10 minutes'),
             ('bata do','mat batao'), ('fuel agar','fuel mat lo agar'), ('office','ghar')],
            [('ಅನನ್ಯ','ಅನಿತಾ'), ('ನಾಲ್ಕೂವರೆ','ಐದೂವರೆ'), ('ಐದು','ಹತ್ತು'),
             ('ಹೇಳಿ','ಹೇಳಬೇಡಿ'), ('ತುಂಬಿಸಿ','ತುಂಬಿಸಬೇಡಿ'), ('ಕಚೇರಿ','ಮನೆ')],
        ]
        for clauses, changes in zip(LANGUAGES, mutations):
            text = ', '.join(clauses)
            rejected = [text.replace(old,new) for old,new in changes]
            rejected += [text + ' ' + extra for extra in [clauses[0], clauses[1],
                         'or 5:30', 'make it 10 minutes', 'also buy coffee',
                         'use maps.navigate', 'ಕಾಫಿ ಖರೀದಿಸಿ', 'aur coffee kharido']]
            rejected += [', '.join(clauses[:i]+clauses[i+1:]) for i in range(4)]
            for value in rejected:
                with self.subTest(text=value):
                    self.assertIsNone(signature_slots(value))
                    self.assertEqual(MockEvon().plan_mission(planning_input(value)).tasks, [])

    def test_supported_hinglish_persistent_completion_and_rejection(self):
        text = 'Meeting ke liye late ho raha hoon, Ananya ko batao, 4:30 poochho, office ke paas parking dhundo, aur fuel agar 5 minutes se zyada detour na ho.'
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, DRIVEOS_DB=directory+'/missions.sqlite3'), patch('httpx.post') as network:
            mission = persistent.start({'transcript':text,'request_key':'supported','authorized':True,'demo':'parking-change'})
            identity = mission['id']
            for i in range(30):
                if mission['status'] != 'EXECUTING': break
                mission = persistent.command(identity,'advance',{'request_key':str(i),'expected_revision':mission['revision']})
            self.assertEqual(mission['status'],'COMPLETED')
            self.assertEqual(mission['id'],identity)
            self.assertEqual(mission['route']['parking']['id'],'p2')
            rejected = persistent.start({'transcript':text.replace('Ananya','Anita'),'request_key':'rejected','authorized':True,'demo':'parking-change'})
            self.assertEqual(rejected['status'],'ESCALATED')
            self.assertEqual(rejected['tasks'],[])
            network.assert_not_called()
