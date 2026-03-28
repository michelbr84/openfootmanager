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
from typing import Optional

from .event import EventOutcome
from .event_type import EventType


class CommentaryGenerator:
    """Generates rich, varied match commentary from event types and outcomes."""

    TEMPLATES: dict[tuple[EventType, EventOutcome], list[str]] = {
        # ── Pass events ──────────────────────────────────────────────
        (EventType.PASS, EventOutcome.PASS_SUCCESS): [
            "Nice pass from {player} to find the teammate.",
            "{player} threads the ball through to a teammate.",
            "Good distribution from {player}, keeping possession for {team}.",
            "{player} picks out the pass beautifully.",
            "Tidy work from {player}, the ball moves on for {team}.",
        ],
        (EventType.PASS, EventOutcome.PASS_MISS): [
            "{player}'s pass goes astray.",
            "Poor delivery from {player}, the ball rolls out of play.",
            "{player} misplaces the pass completely.",
            "That's a wayward ball from {player}.",
        ],
        (EventType.PASS, EventOutcome.PASS_INTERCEPT): [
            "{defender} reads the pass and intercepts!",
            "Intercepted! {defender} steps in to cut out {player}'s pass.",
            "{defender} anticipates the pass from {player} and wins the ball.",
            "Great reading of the game by {defender}, {player}'s pass is picked off.",
        ],
        (EventType.PASS, EventOutcome.PASS_OFFSIDE): [
            "The flag is up! Offside called after {player}'s pass.",
            "{player}'s pass finds a teammate but the linesman flags for offside.",
            "Offside! The run was too early after {player}'s through ball.",
        ],
        # ── Shot events ──────────────────────────────────────────────
        (EventType.SHOT, EventOutcome.GOAL): [
            "GOAL! {player} scores for {team}!",
            "What a strike from {player}! The net bulges!",
            "It's in! {player} finds the back of the net for {team}!",
            "GOAL! Brilliant finish from {player}! {team} celebrate!",
            "{player} makes no mistake! GOAL for {team}!",
        ],
        (EventType.SHOT, EventOutcome.OWN_GOAL): [
            "Oh no! It's an own goal! {defender} puts it into the wrong net!",
            "Disaster for {defender}! That's an own goal!",
            "It's gone in off {defender}! Own goal!",
        ],
        (EventType.SHOT, EventOutcome.SHOT_SAVED): [
            "Great save! The keeper denies {player}!",
            "Saved! The goalkeeper gets down well to stop {player}'s effort.",
            "{player}'s shot is parried away by the keeper.",
            "What a stop! {player} thought that was in!",
        ],
        (EventType.SHOT, EventOutcome.SHOT_SAVED_SECURED): [
            "The keeper holds on to {player}'s shot. Safe hands.",
            "Good save and the goalkeeper gathers it cleanly.",
            "{player}'s effort is comfortably held by the keeper.",
        ],
        (EventType.SHOT, EventOutcome.SHOT_MISS): [
            "{player} fires wide of the target.",
            "Off target! {player}'s shot drifts harmlessly wide.",
            "{player} drags the shot wide. A missed opportunity for {team}.",
            "That's over the bar from {player}. Not the best effort.",
            "{player} blazes it over! {team} won't be happy with that.",
        ],
        (EventType.SHOT, EventOutcome.SHOT_BLOCKED): [
            "{defender} blocks the shot from {player}!",
            "Blocked! {defender} throws a body in the way of {player}'s strike.",
            "{player} shoots but {defender} gets a vital block in.",
            "Great defensive work by {defender} to deny {player}.",
        ],
        (EventType.SHOT, EventOutcome.SHOT_BLOCKED_CHANGE_POSSESSION): [
            "{defender} blocks it and {opponent} clear the danger.",
            "The shot is blocked by {defender} and the ball is swept away.",
            "{defender} gets the block and {opponent} recover possession.",
        ],
        (EventType.SHOT, EventOutcome.SHOT_BLOCKED_BACK): [
            "The shot is blocked but it comes back to {team}!",
            "{defender} blocks but the ball ricochets back into the danger area!",
            "It falls kindly for {team} after the block.",
        ],
        (EventType.SHOT, EventOutcome.SHOT_ON_GOAL): [
            "{player} gets a shot away on target!",
            "{player} strikes towards goal!",
            "Here comes the shot from {player}!",
        ],
        (EventType.SHOT, EventOutcome.SHOT_HIT_POST): [
            "Off the post! {player} so close!",
            "The woodwork saves {opponent}! {player} hits the post!",
            "Agonizing! {player}'s shot rattles the upright!",
            "Post! {player} can't believe it hasn't gone in!",
        ],
        (EventType.SHOT, EventOutcome.SHOT_HIT_POST_CHANGE_POSSESSION): [
            "Off the post and {opponent} scramble the ball clear!",
            "It hits the woodwork and bounces away. {opponent} recover.",
            "{player} strikes the post and {opponent} breathe a sigh of relief.",
        ],
        (EventType.SHOT, EventOutcome.SHOT_LEFT_CORNER_KICK): [
            "{player}'s shot is deflected behind for a corner on the left.",
            "Corner kick to {team}! The shot was turned behind on the left side.",
            "The keeper tips it round the post. Corner to {team} on the left.",
        ],
        (EventType.SHOT, EventOutcome.SHOT_RIGHT_CORNER_KICK): [
            "{player}'s shot is deflected behind for a corner on the right.",
            "Corner kick to {team}! Turned behind on the right side.",
            "Good save pushes it for a corner on the right. {team} will deliver.",
        ],
        (EventType.SHOT, EventOutcome.SHOT_GOAL_KICK): [
            "Well wide. Goal kick to {opponent}.",
            "{player}'s shot is way off target. Goal kick.",
            "That effort never troubled the keeper. Goal kick to {opponent}.",
        ],
        # ── Dribble events ───────────────────────────────────────────
        (EventType.DRIBBLE, EventOutcome.DRIBBLE_SUCCESS): [
            "{player} beats the defender with skill!",
            "Brilliant footwork from {player} to get past the challenge!",
            "{player} dances past {defender} with ease!",
            "What a run! {player} leaves {defender} trailing!",
            "{player} shows great close control to skip past the tackle.",
        ],
        (EventType.DRIBBLE, EventOutcome.DRIBBLE_FAIL): [
            "{defender} dispossesses {player}.",
            "{player} tries to dribble but {defender} makes a clean tackle.",
            "Good defending from {defender}, {player} loses the ball.",
            "{defender} reads {player}'s move and wins possession.",
        ],
        # ── Cross events ─────────────────────────────────────────────
        (EventType.CROSS, EventOutcome.CROSS_SUCCESS): [
            "Excellent cross delivered by {player}!",
            "{player} whips in a dangerous cross from the {position}!",
            "Great delivery from {player}, it finds a teammate in the box!",
            "{player} floats in a lovely cross for {team}.",
        ],
        (EventType.CROSS, EventOutcome.CROSS_MISS): [
            "{player}'s cross sails over everyone.",
            "Overhit from {player}, the cross is too deep.",
            "Poor delivery from {player}, nobody can reach the cross.",
            "{player}'s cross drifts harmlessly behind for a goal kick.",
        ],
        (EventType.CROSS, EventOutcome.CROSS_INTERCEPT): [
            "{defender} gets up well to head the cross away.",
            "The cross from {player} is cut out by {defender}.",
            "{defender} clears the dangerous cross from {player}.",
            "Intercepted! {defender} deals with the cross comfortably.",
        ],
        (EventType.CROSS, EventOutcome.CROSS_OFFSIDE): [
            "Offside! The attacker was ahead of the ball when {player} crossed.",
            "The flag goes up as the cross comes in from {player}. Offside.",
            "{player}'s cross finds a teammate but the offside flag denies {team}.",
        ],
        # ── Foul events ──────────────────────────────────────────────
        (EventType.FOUL, EventOutcome.FOUL_WARNING): [
            "The referee has a word with {player} after that challenge.",
            "Foul by {player}. The referee issues a warning.",
            "{player} catches {defender} late. Just a talking-to from the ref.",
            "Free kick awarded. {player} escapes with a warning.",
        ],
        (EventType.FOUL, EventOutcome.FOUL_YELLOW_CARD): [
            "Yellow card! {player} goes into the book!",
            "The referee shows {player} a yellow card for that foul on {defender}.",
            "Booking! {player} is cautioned. A reckless challenge.",
            "{player} picks up a yellow card. Must be careful now.",
            "Into the book! {player} is shown the yellow card by the referee.",
        ],
        (EventType.FOUL, EventOutcome.FOUL_RED_CARD): [
            "Red card! {player} is sent off!",
            "A straight red! {player} has to go after that terrible challenge!",
            "Off you go! The referee shows {player} a red card!",
            "{player} sees red! {team} are down to ten men!",
            "Sent off! {player} leaves the pitch in disgrace!",
        ],
        # ── Free kick events ─────────────────────────────────────────
        (EventType.FREE_KICK, EventOutcome.GOAL): [
            "GOAL! {player} scores directly from the free kick! Stunning!",
            "What a free kick from {player}! Right into the top corner!",
            "Over the wall and in! {player} scores a superb free kick!",
        ],
        (EventType.FREE_KICK, EventOutcome.SHOT_MISS): [
            "{player}'s free kick flies over the bar.",
            "The free kick from {player} hits the wall.",
            "{player} sends the free kick wide. Wasted opportunity.",
        ],
        (EventType.FREE_KICK, EventOutcome.SHOT_SAVED): [
            "The keeper saves {player}'s free kick!",
            "Good free kick from {player} but the keeper is equal to it.",
            "{player}'s free kick is pushed away by the goalkeeper.",
        ],
        (EventType.FREE_KICK, EventOutcome.PASS_SUCCESS): [
            "{player} plays the free kick short.",
            "Clever free kick from {player}, played to a nearby teammate.",
            "{player} opts for the short free kick to restart play.",
        ],
        (EventType.FREE_KICK, EventOutcome.CROSS_SUCCESS): [
            "{player} delivers the free kick into the box!",
            "Dangerous free kick from {player} into the penalty area!",
            "{player} floats the free kick towards the far post!",
        ],
        # ── Corner kick events ───────────────────────────────────────
        (EventType.CORNER_KICK, EventOutcome.CROSS_SUCCESS): [
            "{player} delivers the corner into a dangerous area!",
            "In-swinging corner from {player}, headed away at the near post!",
            "Good delivery from {player} on the corner kick.",
            "{player} whips in the corner for {team}!",
        ],
        (EventType.CORNER_KICK, EventOutcome.CROSS_MISS): [
            "{player}'s corner is overhit and goes out the other side.",
            "Poor corner from {player}. Easily dealt with.",
            "Wayward delivery from {player} on the corner kick.",
        ],
        (EventType.CORNER_KICK, EventOutcome.CROSS_INTERCEPT): [
            "The corner is punched clear by the goalkeeper!",
            "{defender} rises highest to clear the corner.",
            "Good defensive header from {defender} to clear the corner.",
        ],
        (EventType.CORNER_KICK, EventOutcome.GOAL): [
            "GOAL from the corner! {player}'s delivery is headed home!",
            "They've scored from the set piece! The corner results in a goal!",
            "What a corner from {player}! It ends up in the back of the net!",
        ],
        (EventType.CORNER_KICK, EventOutcome.PASS_SUCCESS): [
            "{player} plays the corner short to a teammate.",
            "Short corner from {player}, keeping it simple.",
        ],
        # ── Penalty kick events ──────────────────────────────────────
        (EventType.PENALTY_KICK, EventOutcome.GOAL): [
            "GOAL! {player} converts the penalty!",
            "{player} sends the keeper the wrong way! Penalty scored!",
            "Cool as you like! {player} slots home the penalty!",
            "No mistake from {player}! The penalty is dispatched!",
        ],
        (EventType.PENALTY_KICK, EventOutcome.SHOT_SAVED): [
            "Saved! The keeper dives the right way to deny {player}!",
            "Penalty saved! What a moment! {player} is denied!",
            "The goalkeeper is the hero! {player}'s penalty is stopped!",
        ],
        (EventType.PENALTY_KICK, EventOutcome.SHOT_MISS): [
            "{player} blazes the penalty over the bar!",
            "Missed! {player} puts the penalty wide!",
            "{player} skies the penalty! Unbelievable!",
        ],
        (EventType.PENALTY_KICK, EventOutcome.SHOT_HIT_POST): [
            "Off the post! {player}'s penalty comes back off the woodwork!",
            "The penalty hits the post! {player} can't believe it!",
        ],
        # ── Goal kick events ─────────────────────────────────────────
        (EventType.GOAL_KICK, EventOutcome.PASS_SUCCESS): [
            "Goal kick taken by the keeper, finds a teammate.",
            "The goalkeeper sends it long from the goal kick.",
            "Short goal kick, the defense plays it out from the back.",
        ],
        (EventType.GOAL_KICK, EventOutcome.PASS_MISS): [
            "The goal kick is contested and goes out for a throw.",
            "Long goal kick, but nobody can bring it under control.",
        ],
        (EventType.GOAL_KICK, EventOutcome.PASS_INTERCEPT): [
            "The goal kick is won by {defender} in the air.",
            "{defender} challenges for the goal kick and wins possession.",
        ],
    }

    KICKOFF_TEMPLATES: list[str] = [
        "And we're underway! {team} kick off!",
        "The referee blows the whistle and {team} get us started!",
        "{team} kick off the match! Here we go!",
        "The game begins! {team} have the first touch.",
    ]

    HALFTIME_TEMPLATES: list[str] = [
        "The referee blows for half time. {home} {home_score} - {away_score} {away}.",
        "Half time! The score is {home} {home_score}, {away} {away_score}.",
        "That's the break. {home} {home_score} - {away_score} {away} at the interval.",
        "The first half comes to an end. {home} {home_score} - {away_score} {away}.",
    ]

    FULLTIME_TEMPLATES: list[str] = [
        "Full time! {home} {home_score} - {away_score} {away}.",
        "It's all over! The final score: {home} {home_score} - {away_score} {away}.",
        "The referee blows the final whistle! {home} {home_score} - {away_score} {away}.",
        "That's it! Final score: {home} {home_score}, {away} {away_score}.",
    ]

    SUBSTITUTION_TEMPLATES: list[str] = [
        "Substitution for {team}. {player_out} is replaced by {player_in}.",
        "{player_in} comes on for {player_out}. A change for {team}.",
        "{team} make a substitution: {player_out} off, {player_in} on.",
        "Here comes {player_in}, replacing {player_out} for {team}.",
        "A tactical change for {team}. {player_out} makes way for {player_in}.",
    ]

    INJURY_TEMPLATES: list[str] = [
        "{player} is down and in some pain. It looks like a {injury_type}.",
        "Bad news for {player}, who appears to have suffered a {injury_type}.",
        "The physio is on the pitch attending to {player}. A {injury_type} is suspected.",
        "Oh no, {player} is struggling with a {injury_type}. This doesn't look good.",
        "{player} limps off the field. Early reports suggest a {injury_type}.",
    ]

    def generate(
        self,
        event_type: EventType,
        outcome: EventOutcome,
        **kwargs: str,
    ) -> str:
        """Pick a random template for the event/outcome pair and fill placeholders.

        Supported keyword arguments: player, defender, team, opponent, minute, position.
        Missing placeholders are silently replaced with empty strings.
        """
        key = (event_type, outcome)
        templates = self.TEMPLATES.get(key)
        if not templates:
            return ""
        template = random.choice(templates)
        # Replace only the placeholders that are present in kwargs
        for placeholder in ("player", "defender", "team", "opponent", "minute", "position"):
            token = "{" + placeholder + "}"
            if token in template:
                template = template.replace(token, str(kwargs.get(placeholder, "")))
        return template

    def generate_kickoff(self, team_name: str) -> str:
        """Generate a kick-off commentary line."""
        template = random.choice(self.KICKOFF_TEMPLATES)
        return template.replace("{team}", team_name)

    def generate_halftime(
        self,
        home: str,
        away: str,
        home_score: int,
        away_score: int,
    ) -> str:
        """Generate a half-time commentary line."""
        template = random.choice(self.HALFTIME_TEMPLATES)
        return template.format(
            home=home,
            away=away,
            home_score=home_score,
            away_score=away_score,
        )

    def generate_fulltime(
        self,
        home: str,
        away: str,
        home_score: int,
        away_score: int,
    ) -> str:
        """Generate a full-time commentary line."""
        template = random.choice(self.FULLTIME_TEMPLATES)
        return template.format(
            home=home,
            away=away,
            home_score=home_score,
            away_score=away_score,
        )

    def generate_substitution(
        self,
        player_out: str,
        player_in: str,
        team: str,
    ) -> str:
        """Generate a substitution commentary line."""
        template = random.choice(self.SUBSTITUTION_TEMPLATES)
        return template.format(
            player_out=player_out,
            player_in=player_in,
            team=team,
        )

    def generate_injury(self, player: str, injury_type: str) -> str:
        """Generate an injury commentary line."""
        template = random.choice(self.INJURY_TEMPLATES)
        return template.format(player=player, injury_type=injury_type)
