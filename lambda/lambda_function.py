# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging
import ask_sdk_core.utils as ask_utils
import os
import json
import locale
import requests
import calendar
import gettext
from datetime import datetime
from pytz import timezone
from ask_sdk_s3.adapter import S3Adapter
s3_adapter = S3Adapter(bucket_name=os.environ["S3_PERSISTENCE_BUCKET"])

from alexa import data

from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractRequestInterceptor, AbstractExceptionHandler)
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

from ask_sdk_core.utils import is_request_type, is_intent_name

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# All friends are stored as {FriendName : {"propertyName":"propertyValue"}}

class LaunchRequestHandler(AbstractRequestHandler):
    """
    Handler for Skill Launch
    """

    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        data = handler_input.attributes_manager.request_attributes["_"]
        if(len(handler_input.attributes_manager.persistent_attributes) > 0):
            speech = data["WELCOME_MSG_SHORT"]
        else:
            speech = data["WELCOME_MSG"]    
        reprompt = data["WELCOME_REPROMPT_MSG"]

        handler_input.response_builder.speak(speech).ask(reprompt)
        return handler_input.response_builder.response

class AddFriendIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AddFriendIntent")(handler_input)
        
    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        friendToAdd = slots["friend"].value
        
        friend_dictionary_local = handler_input.attributes_manager.persistent_attributes.copy()
        if friendToAdd in friend_dictionary_local:
            return (
                handler_input
                    .response_builder
                    .speak("Name already present in memory")
                    .ask("What else do you want to do?")
                    .response
            )
        
        friend_dictionary_local[friendToAdd] = {}
        
        attributes_manager = handler_input.attributes_manager
        attributes_manager.persistent_attributes = friend_dictionary_local
        attributes_manager.save_persistent_attributes()
        
        return (
            handler_input.response_builder
                .speak("Added friend with name {}".format(friendToAdd))
                .ask("What else do you want to do?")
                .response
        )
        
class AddFriendBirthdayIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AddFriendBirthdayIntent")(handler_input)
        
    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        friendName = slots["friend"].value
        day = slots["day"].value
        month = slots["month"].value
        year = slots["year"].value
        
        friend_dictionary_local = handler_input.attributes_manager.persistent_attributes.copy()
        if(friend_dictionary_local.get(friendName, -1) != -1):
            response_message = "I added {} to your friends which was not present.".format(friendName);
        else:
            response_message = ""
        friend_dictionary_local[friendName] = {"day":day, "month":month, "year":year}
        
        response_message += " I will remember your friend {} was born on {}{}{}".format(friendName, day, month, year)
        handler_input.attributes_manager.persistent_attributes = friend_dictionary_local
        handler_input.attributes_manager.save_persistent_attributes()   
        
        return (
            handler_input.response_builder
                .speak(response_message)
                .ask("What else do you want to do?")
                .response
        )
  
class SpeakAllFriendNamesIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("SpeakAllFriendNamesIntent")(handler_input)
        
    def handle(self, handler_input):
        friend_dictionary_local = handler_input.attributes_manager.persistent_attributes.copy()
        number_of_friends = len(friend_dictionary_local)
        response = "You have {} friends. There names are ".format(number_of_friends)
        for key, value in friend_dictionary_local.items():
            response = response + key + ", "
        response = response + "."
        
        return (
            handler_input.response_builder
                .speak(response)
                .ask("What else do you want to do?")
                .response
        )   

class ListAllBirthdaysIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("ListAllBirthdaysIntent")(handler_input)
        
    def handle(self, handler_input):
        friend_dictionary_local = handler_input.attributes_manager.persistent_attributes.copy()
        
        response_message = ""
        birthdays_present = 0
        for key, value in friend_dictionary_local.items():
            if("day" in value, "month" in value, "year" in value):
                response_message += "{} was born on {}{}{}. ".format(key, value["day"], value["month"], value["year"])
                birthdays_present += 1
        reponse_message = "Out of {} friends, {} have birthdays stored. ".format(len(friend_dictionary_local), birthdays_present) + response_message
        
        return (
            handler_input.response_builder
                .speak(reponse_message)
                .ask("What else do you want to do?")
                .response
        )   

class DeleteAllIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("DeleteAllIntent")(handler_input)
        
    def handle(self, handler_input):
        handler_input.attributes_manager.persistent_attributes = {}
        handler_input.attributes_manager.save_persistent_attributes()
        
        return (
            handler_input.response_builder
                .speak("Deleted all friends.")
                .ask("What else do you want to do?")
                .response
        )

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        data = handler_input.attributes_manager.request_attributes["_"]
        speak_output = data["HELP_MSG"]

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        data = handler_input.attributes_manager.request_attributes["_"]
        speak_output = data["GOODBYE_MSG"]

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        data = handler_input.attributes_manager.request_attributes["_"]
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = data["REFLECTOR_MSG"].format(intent_name)

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(handler_input, exc_info=True)
        logger.error(exception, exc_info=True)
        data = handler_input.attributes_manager.request_attributes["_"]
        speak_output = data["ERROR_MSG"]

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


class LocalizationInterceptor(AbstractRequestInterceptor):
    """
    Add function to request attributes, that can load locale specific data.
    """

    def process(self, handler_input):
        skill_locale = handler_input.request_envelope.request.locale

        # localized strings stored in language_strings.json
        with open("language_strings.json") as language_prompts:
            language_data = json.load(language_prompts)
        # set default translation data to broader translation
        data = language_data[skill_locale[:2]]
        # if a more specialized translation exists, then select it instead
        # example: "fr-CA" will pick "fr" translations first, but if "fr-CA" translation exists,
        #          then pick that instead
        if skill_locale in language_data:
            data.update(language_data[skill_locale])
        handler_input.attributes_manager.request_attributes["_"] = data

        # configure the runtime to treat time according to the skill locale
        skill_locale = skill_locale.replace('-','_')
        locale.setlocale(locale.LC_TIME, skill_locale)
        

sb = CustomSkillBuilder(persistence_adapter=s3_adapter)

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(AddFriendIntentHandler())
sb.add_request_handler(AddFriendBirthdayIntentHandler())
sb.add_request_handler(SpeakAllFriendNamesIntentHandler())
sb.add_request_handler(ListAllBirthdaysIntentHandler())
sb.add_request_handler(DeleteAllIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn’t override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

sb.add_global_request_interceptor(LocalizationInterceptor())


lambda_handler = sb.lambda_handler()