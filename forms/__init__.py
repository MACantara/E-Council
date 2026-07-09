"""Flask-WTF forms package for E-Council."""

from forms.auth import SignupForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from forms.concept_papers import ConceptPaperForm
from forms.documentation import DocumentationForm
from forms.events import EventForm, TransactionForm
from forms.financial import FinancialReportForm
from forms.meetings import MinutesOfTheMeetingForm
from forms.board_resolutions import BoardResolutionForm

__all__ = [
    'SignupForm',
    'LoginForm',
    'ForgotPasswordForm',
    'ResetPasswordForm',
    'ConceptPaperForm',
    'DocumentationForm',
    'EventForm',
    'TransactionForm',
    'FinancialReportForm',
    'MinutesOfTheMeetingForm',
    'BoardResolutionForm',
]
