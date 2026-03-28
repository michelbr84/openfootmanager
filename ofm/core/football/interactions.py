#      Openfoot Manager - A free and open source soccer management simulation
#      Copyright (C) 2020-2025  Pedrenrique G. Guimarães
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.
import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class InteractionType(Enum):
    PRESS_CONFERENCE = auto()
    PLAYER_TALK = auto()
    TEAM_TALK = auto()


class MoraleEffect(Enum):
    VERY_NEGATIVE = -2
    NEGATIVE = -1
    NEUTRAL = 0
    POSITIVE = 1
    VERY_POSITIVE = 2


class TalkType(Enum):
    PRAISE = auto()
    CRITICIZE = auto()
    ENCOURAGE = auto()
    WARN = auto()
    PROMISE = auto()


class TeamTalkType(Enum):
    MOTIVATE = auto()
    CALM_DOWN = auto()
    FOCUS = auto()
    ENCOURAGE = auto()
    DEMAND_MORE = auto()


@dataclass
class PressResponse:
    text: str
    morale_effect: MoraleEffect
    reputation_change: int


@dataclass
class PressQuestion:
    question: str
    topic: str
    options: list[PressResponse]


# ---------------------------------------------------------------------------
# Press Conference
# ---------------------------------------------------------------------------

class PressConference:
    """Generates contextual press conferences with multiple-choice responses."""

    QUESTIONS: list[PressQuestion] = [
        # ── Pre-match ─────────────────────────────────────────────
        PressQuestion(
            question="How do you rate your chances in the upcoming match?",
            topic="pre_match",
            options=[
                PressResponse("We're confident and ready to win.", MoraleEffect.POSITIVE, 1),
                PressResponse("It will be a tough game, but we'll give our best.", MoraleEffect.NEUTRAL, 0),
                PressResponse("We need to be realistic about our limitations.", MoraleEffect.NEGATIVE, -1),
            ],
        ),
        PressQuestion(
            question="Any injury concerns ahead of the match?",
            topic="pre_match",
            options=[
                PressResponse("The squad is fully fit and raring to go.", MoraleEffect.POSITIVE, 0),
                PressResponse("We have a few knocks but nothing serious.", MoraleEffect.NEUTRAL, 0),
                PressResponse("We're dealing with several injuries at the moment.", MoraleEffect.NEGATIVE, 0),
            ],
        ),
        PressQuestion(
            question="What's your game plan for tomorrow?",
            topic="pre_match",
            options=[
                PressResponse("We're going out to attack from the first whistle.", MoraleEffect.POSITIVE, 1),
                PressResponse("We'll assess the situation and adapt accordingly.", MoraleEffect.NEUTRAL, 0),
                PressResponse("Defensive solidity will be our priority.", MoraleEffect.NEUTRAL, -1),
            ],
        ),
        PressQuestion(
            question="How important is this match for the season?",
            topic="pre_match",
            options=[
                PressResponse("Every match is a final for us. We treat them all the same.", MoraleEffect.POSITIVE, 1),
                PressResponse("It's an important fixture, but the season is long.", MoraleEffect.NEUTRAL, 0),
                PressResponse("I don't want to put too much pressure on the players.", MoraleEffect.NEGATIVE, 0),
            ],
        ),
        # ── Post-match win ────────────────────────────────────────
        PressQuestion(
            question="Great result today, how do you feel?",
            topic="post_match_win",
            options=[
                PressResponse("Fantastic! The players were magnificent today.", MoraleEffect.VERY_POSITIVE, 2),
                PressResponse("A good result. We did what we needed to do.", MoraleEffect.POSITIVE, 1),
                PressResponse("Happy with the points but there's room for improvement.", MoraleEffect.NEUTRAL, 0),
            ],
        ),
        PressQuestion(
            question="Who was your man of the match?",
            topic="post_match_win",
            options=[
                PressResponse("I thought the whole team was brilliant today.", MoraleEffect.POSITIVE, 1),
                PressResponse("There were several standout performances.", MoraleEffect.POSITIVE, 0),
                PressResponse("I'd rather focus on the collective effort.", MoraleEffect.NEUTRAL, 0),
            ],
        ),
        PressQuestion(
            question="Is the team building momentum now?",
            topic="post_match_win",
            options=[
                PressResponse("Absolutely! We're on a great run and feeling unstoppable.", MoraleEffect.VERY_POSITIVE, 2),
                PressResponse("We're in good form but must stay grounded.", MoraleEffect.POSITIVE, 1),
                PressResponse("One game at a time, let's not get carried away.", MoraleEffect.NEUTRAL, 0),
            ],
        ),
        # ── Post-match loss ───────────────────────────────────────
        PressQuestion(
            question="Disappointing result, what went wrong?",
            topic="post_match_loss",
            options=[
                PressResponse("We'll bounce back. One bad day doesn't define us.", MoraleEffect.POSITIVE, 0),
                PressResponse("We made too many mistakes and paid the price.", MoraleEffect.NEGATIVE, -1),
                PressResponse("I take full responsibility. I'll fix this.", MoraleEffect.NEUTRAL, 1),
            ],
        ),
        PressQuestion(
            question="Will you make changes for the next game?",
            topic="post_match_loss",
            options=[
                PressResponse("I believe in this squad. They'll respond.", MoraleEffect.POSITIVE, 0),
                PressResponse("I'll be looking at everything, including the lineup.", MoraleEffect.NEUTRAL, 0),
                PressResponse("Major changes are needed. Some players let us down.", MoraleEffect.VERY_NEGATIVE, -1),
            ],
        ),
        PressQuestion(
            question="Are you worried about the team's form?",
            topic="post_match_loss",
            options=[
                PressResponse("Not at all. We have the quality to turn this around.", MoraleEffect.POSITIVE, 1),
                PressResponse("It's a concern, but I trust the process.", MoraleEffect.NEUTRAL, 0),
                PressResponse("I'd be lying if I said I wasn't concerned.", MoraleEffect.NEGATIVE, -1),
            ],
        ),
        PressQuestion(
            question="The fans are unhappy. What do you say to them?",
            topic="post_match_loss",
            options=[
                PressResponse("I understand their frustration. We'll put it right.", MoraleEffect.NEUTRAL, 1),
                PressResponse("We need their support now more than ever.", MoraleEffect.POSITIVE, 0),
                PressResponse("They have every right to be angry after that performance.", MoraleEffect.NEGATIVE, -1),
            ],
        ),
        # ── Transfer ──────────────────────────────────────────────
        PressQuestion(
            question="Are you looking to sign anyone this window?",
            topic="transfer",
            options=[
                PressResponse("We're always looking to improve the squad.", MoraleEffect.POSITIVE, 1),
                PressResponse("If the right player becomes available, we'll be ready.", MoraleEffect.NEUTRAL, 0),
                PressResponse("I'm happy with what we have. No plans to sign anyone.", MoraleEffect.NEUTRAL, -1),
            ],
        ),
        PressQuestion(
            question="There are rumors a key player wants to leave. Any comment?",
            topic="transfer",
            options=[
                PressResponse("Nobody is leaving. The player is fully committed.", MoraleEffect.POSITIVE, 1),
                PressResponse("I won't comment on speculation.", MoraleEffect.NEUTRAL, 0),
                PressResponse("If a player doesn't want to be here, the door is open.", MoraleEffect.NEGATIVE, -1),
            ],
        ),
        PressQuestion(
            question="How do you feel about the transfer budget?",
            topic="transfer",
            options=[
                PressResponse("The board has been very supportive.", MoraleEffect.POSITIVE, 1),
                PressResponse("We work within our means. That's the reality.", MoraleEffect.NEUTRAL, 0),
                PressResponse("I wish we had more to spend, frankly.", MoraleEffect.NEGATIVE, -1),
            ],
        ),
        # ── General ───────────────────────────────────────────────
        PressQuestion(
            question="How's the team spirit at the moment?",
            topic="general",
            options=[
                PressResponse("Brilliant! The dressing room is buzzing.", MoraleEffect.VERY_POSITIVE, 1),
                PressResponse("Good. The lads are working hard every day.", MoraleEffect.POSITIVE, 0),
                PressResponse("There are always things to work on in that department.", MoraleEffect.NEUTRAL, 0),
            ],
        ),
        PressQuestion(
            question="Your thoughts on the league this season?",
            topic="general",
            options=[
                PressResponse("We're aiming for the top. No question about it.", MoraleEffect.POSITIVE, 2),
                PressResponse("It's very competitive. Anything can happen.", MoraleEffect.NEUTRAL, 0),
                PressResponse("It'll be tough, but we'll fight for every point.", MoraleEffect.POSITIVE, 0),
            ],
        ),
        PressQuestion(
            question="How are the young players developing?",
            topic="general",
            options=[
                PressResponse("Some of them are ready to step up right now.", MoraleEffect.POSITIVE, 1),
                PressResponse("They're progressing well. Patience is key.", MoraleEffect.NEUTRAL, 0),
                PressResponse("Youth development is a long-term project.", MoraleEffect.NEUTRAL, 0),
            ],
        ),
        PressQuestion(
            question="What's your relationship like with the board?",
            topic="general",
            options=[
                PressResponse("Excellent. We're fully aligned on the vision.", MoraleEffect.POSITIVE, 2),
                PressResponse("Professional. We communicate regularly.", MoraleEffect.NEUTRAL, 0),
                PressResponse("I'd prefer to keep that between us.", MoraleEffect.NEUTRAL, -1),
            ],
        ),
    ]

    # Map context strings to relevant topics
    _CONTEXT_TOPICS: dict[str, list[str]] = {
        "pre_match": ["pre_match", "general"],
        "post_match_win": ["post_match_win", "general"],
        "post_match_loss": ["post_match_loss", "general"],
        "transfer": ["transfer", "general"],
        "general": ["general"],
    }

    def generate_press_conference(
        self,
        context: str,
        num_questions: int = 4,
    ) -> list[PressQuestion]:
        """Pick 3-5 relevant questions based on the context.

        Args:
            context: One of "pre_match", "post_match_win", "post_match_loss",
                     "transfer", or "general".
            num_questions: How many questions to include (clamped to 3-5).
        """
        num_questions = max(3, min(5, num_questions))
        topics = self._CONTEXT_TOPICS.get(context, ["general"])
        relevant = [q for q in self.QUESTIONS if q.topic in topics]
        if len(relevant) < num_questions:
            # Pad with general questions if needed
            extras = [q for q in self.QUESTIONS if q not in relevant]
            relevant.extend(extras[: num_questions - len(relevant)])
        return random.sample(relevant, min(num_questions, len(relevant)))

    @staticmethod
    def process_response(response: PressResponse) -> dict:
        """Process the chosen response and return its effects.

        Returns:
            dict with keys: morale_change (int), reputation_change (int).
        """
        return {
            "morale_change": response.morale_effect.value,
            "reputation_change": response.reputation_change,
        }


# ---------------------------------------------------------------------------
# Player Interaction
# ---------------------------------------------------------------------------

class PlayerInteraction:
    """Handles one-on-one conversations between manager and players."""

    TALK_OPTIONS: dict[TalkType, dict] = {
        TalkType.PRAISE: {
            "description": "Praise the player for their recent efforts.",
            "base_morale_effect": MoraleEffect.POSITIVE,
            "good_form_bonus": 1,   # Extra morale if player is in good form
            "bad_form_penalty": 0,  # No penalty; praise is well-received regardless
            "responses": {
                "good_form": [
                    "{player} beams with pride. 'Thanks, boss! I'll keep it up.'",
                    "{player} nods confidently. 'I appreciate that, gaffer.'",
                    "{player} smiles. 'That means a lot coming from you.'",
                ],
                "neutral_form": [
                    "{player} seems pleased. 'Cheers, boss. I'll try to do even better.'",
                    "{player} nods. 'Thank you. I'll keep working hard.'",
                ],
                "bad_form": [
                    "{player} looks surprised but grateful. 'Thanks... I needed that.'",
                    "{player} nods quietly. 'I'll try to repay your faith.'",
                ],
            },
        },
        TalkType.CRITICIZE: {
            "description": "Criticize the player's recent performances.",
            "base_morale_effect": MoraleEffect.NEGATIVE,
            "good_form_bonus": -1,  # Criticism hurts more when player is performing
            "bad_form_penalty": 1,  # Player accepts it more when they know they're bad
            "responses": {
                "good_form": [
                    "{player} looks shocked. 'I've been playing well! That's unfair.'",
                    "{player} is visibly upset. 'I don't understand, boss.'",
                ],
                "neutral_form": [
                    "{player} looks down. 'I'll try to do better.'",
                    "{player} shrugs. 'Fair enough. I'll work on it.'",
                ],
                "bad_form": [
                    "{player} nods reluctantly. 'You're right. I need to step up.'",
                    "{player} accepts the criticism. 'I know I can do better.'",
                ],
            },
        },
        TalkType.ENCOURAGE: {
            "description": "Encourage the player to keep going.",
            "base_morale_effect": MoraleEffect.POSITIVE,
            "good_form_bonus": 0,
            "bad_form_penalty": 0,
            "responses": {
                "good_form": [
                    "{player} smiles. 'I'm feeling great, boss. Ready for anything.'",
                    "{player} nods enthusiastically. 'Let's keep this going!'",
                ],
                "neutral_form": [
                    "{player} appreciates the support. 'Thanks, boss. I'll give it my all.'",
                    "{player} seems motivated. 'I won't let you down.'",
                ],
                "bad_form": [
                    "{player} looks relieved. 'Thanks for believing in me, boss.'",
                    "{player} nods. 'I really needed to hear that. I'll turn it around.'",
                ],
            },
        },
        TalkType.WARN: {
            "description": "Warn the player about their attitude or performance.",
            "base_morale_effect": MoraleEffect.NEGATIVE,
            "good_form_bonus": -1,
            "bad_form_penalty": 0,
            "responses": {
                "good_form": [
                    "{player} is confused. 'What have I done wrong?'",
                    "{player} frowns. 'I thought I was doing well...'",
                ],
                "neutral_form": [
                    "{player} takes the warning on board. 'Understood, boss.'",
                    "{player} nods seriously. 'I hear you. I'll be careful.'",
                ],
                "bad_form": [
                    "{player} looks worried. 'I'll sort myself out, boss.'",
                    "{player} accepts the warning. 'Point taken.'",
                ],
            },
        },
        TalkType.PROMISE: {
            "description": "Make a promise to the player (e.g., more playing time).",
            "base_morale_effect": MoraleEffect.VERY_POSITIVE,
            "good_form_bonus": 0,
            "bad_form_penalty": 0,
            "responses": {
                "good_form": [
                    "{player} grins. 'That's great to hear, boss!'",
                    "{player} looks delighted. 'I won't let you down!'",
                ],
                "neutral_form": [
                    "{player} nods. 'I appreciate that, boss. I'll earn it.'",
                    "{player} seems happy. 'Thanks for the opportunity.'",
                ],
                "bad_form": [
                    "{player} is grateful. 'I'll work hard to deserve it.'",
                    "{player} perks up. 'Thank you, boss. I'll prove myself.'",
                ],
            },
        },
    }

    TEAM_TALK_OPTIONS: dict[TeamTalkType, dict] = {
        TeamTalkType.MOTIVATE: {
            "description": "Fire up the team before the match.",
            "base_morale_effect": MoraleEffect.POSITIVE,
            "responses": [
                "The team looks fired up and ready to go!",
                "The players respond with a roar of approval!",
                "You can see the determination in their eyes.",
            ],
        },
        TeamTalkType.CALM_DOWN: {
            "description": "Calm the team's nerves.",
            "base_morale_effect": MoraleEffect.NEUTRAL,
            "responses": [
                "The players seem more relaxed now.",
                "The tension in the dressing room eases.",
                "The team takes a collective deep breath.",
            ],
        },
        TeamTalkType.FOCUS: {
            "description": "Demand the team stays focused.",
            "base_morale_effect": MoraleEffect.NEUTRAL,
            "responses": [
                "The players nod, concentrated and alert.",
                "The message lands. Everyone knows their job.",
                "You can see the focus sharpen in their expressions.",
            ],
        },
        TeamTalkType.ENCOURAGE: {
            "description": "Encourage the team to believe in themselves.",
            "base_morale_effect": MoraleEffect.POSITIVE,
            "responses": [
                "The dressing room buzzes with positive energy!",
                "The players look at each other with renewed belief.",
                "Confidence fills the room.",
            ],
        },
        TeamTalkType.DEMAND_MORE: {
            "description": "Tell the team their performance is not good enough.",
            "base_morale_effect": MoraleEffect.NEGATIVE,
            "responses": [
                "Some players look stung, but they know you're right.",
                "The dressing room goes quiet. The message is received.",
                "A few players look uncomfortable, but most nod in agreement.",
            ],
        },
    }

    def _determine_form(self, player_form: Optional[float] = None) -> str:
        """Classify player form into good / neutral / bad."""
        if player_form is None:
            return "neutral_form"
        if player_form >= 7.0:
            return "good_form"
        if player_form <= 4.0:
            return "bad_form"
        return "neutral_form"

    def talk_to_player(
        self,
        player_name: str,
        talk_type: TalkType,
        player_form: Optional[float] = None,
    ) -> dict:
        """Conduct a one-on-one talk with a player.

        Args:
            player_name: Display name of the player.
            talk_type: The kind of talk to have.
            player_form: Optional average rating (0-10) used to pick contextual responses.

        Returns:
            dict with keys: response_text (str), morale_change (int).
        """
        option = self.TALK_OPTIONS[talk_type]
        form_key = self._determine_form(player_form)

        # Pick a response template
        responses = option["responses"][form_key]
        response_text = random.choice(responses).replace("{player}", player_name)

        # Calculate morale change
        base = option["base_morale_effect"].value
        if form_key == "good_form":
            base += option["good_form_bonus"]
        elif form_key == "bad_form":
            base += option["bad_form_penalty"]

        return {
            "response_text": response_text,
            "morale_change": base,
        }

    def team_talk(
        self,
        talk_type: TeamTalkType,
        context: Optional[str] = None,
    ) -> dict:
        """Deliver a pre-match or half-time team talk.

        Args:
            talk_type: The style of team talk.
            context: Optional context string (e.g., "halftime_winning").

        Returns:
            dict with keys: response_text (str), morale_change (int).
        """
        option = self.TEAM_TALK_OPTIONS[talk_type]
        response_text = random.choice(option["responses"])
        morale_change = option["base_morale_effect"].value

        # Context-based adjustments
        if context == "halftime_winning" and talk_type == TeamTalkType.DEMAND_MORE:
            morale_change -= 1  # Players resent being criticized while winning
        elif context == "halftime_losing" and talk_type == TeamTalkType.MOTIVATE:
            morale_change += 1  # Extra boost when team needs it most

        return {
            "response_text": response_text,
            "morale_change": morale_change,
        }


# ---------------------------------------------------------------------------
# Interaction Manager
# ---------------------------------------------------------------------------

class InteractionManager:
    """Central manager that tracks all press conferences, player talks, and
    team talks throughout a career save."""

    def __init__(self) -> None:
        self.interaction_history: list[dict] = []
        self._press_conference = PressConference()
        self._player_interaction = PlayerInteraction()

    def conduct_press_conference(
        self,
        context: str,
        num_questions: int = 4,
    ) -> list[PressQuestion]:
        """Generate a press conference and log the event.

        Args:
            context: One of "pre_match", "post_match_win", "post_match_loss",
                     "transfer", or "general".
            num_questions: Number of questions (3-5).

        Returns:
            A list of PressQuestion objects, each with response options.
        """
        questions = self._press_conference.generate_press_conference(context, num_questions)
        self.interaction_history.append({
            "type": InteractionType.PRESS_CONFERENCE.name,
            "context": context,
            "num_questions": len(questions),
        })
        return questions

    def submit_press_response(self, response: PressResponse) -> dict:
        """Process a single press response and return effects."""
        result = PressConference.process_response(response)
        self.interaction_history.append({
            "type": InteractionType.PRESS_CONFERENCE.name,
            "action": "response",
            "morale_change": result["morale_change"],
            "reputation_change": result["reputation_change"],
        })
        return result

    def talk_to_player(
        self,
        player_name: str,
        talk_type: TalkType,
        player_form: Optional[float] = None,
    ) -> dict:
        """Talk to an individual player and log the interaction.

        Returns:
            dict with keys: response_text (str), morale_change (int).
        """
        result = self._player_interaction.talk_to_player(player_name, talk_type, player_form)
        self.interaction_history.append({
            "type": InteractionType.PLAYER_TALK.name,
            "player": player_name,
            "talk_type": talk_type.name,
            "morale_change": result["morale_change"],
        })
        return result

    def give_team_talk(
        self,
        talk_type: TeamTalkType,
        context: Optional[str] = None,
    ) -> dict:
        """Deliver a team talk and log the interaction.

        Returns:
            dict with keys: response_text (str), morale_change (int).
        """
        result = self._player_interaction.team_talk(talk_type, context)
        self.interaction_history.append({
            "type": InteractionType.TEAM_TALK.name,
            "talk_type": talk_type.name,
            "context": context,
            "morale_change": result["morale_change"],
        })
        return result

    def serialize(self) -> dict:
        """Serialize the interaction manager state to a dictionary."""
        return {
            "interaction_history": list(self.interaction_history),
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "InteractionManager":
        """Reconstruct an InteractionManager from a serialized dictionary."""
        manager = cls()
        manager.interaction_history = data.get("interaction_history", [])
        return manager
