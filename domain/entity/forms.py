from datetime import datetime

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import (
    BooleanField,
    DateTimeLocalField,
    FileField,
    HiddenField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
    ValidationError,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    Optional,
)

PASSWORD_LENGTH_MESSAGE = "Password must be between 8 and 255 characters"
NON_SPORTS_ACTIVITY_TYPE = "Non Sports"
SAVE_CHANGES_MESSAGE = "Save Changes"


class RegisterForm(FlaskForm):
    name = StringField(
        "Name",
        validators=[
            DataRequired(message="Name is required"),
            Length(max=50, message="Name must be less than 50 characters"),
        ],
    )
    email = StringField(
        "Email Address",
        validators=[
            DataRequired(message="Email is required"),
            Email(message="Enter a valid email"),
            Length(max=254, message="Email must be less than 254 characters"),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Password is required"),
            Length(min=8, max=255, message=PASSWORD_LENGTH_MESSAGE),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(message="Please confirm your password"),
            EqualTo("password", message="Passwords must match"),
        ],
    )
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField(
        "Email Address",
        validators=[
            DataRequired(message="Email is required."),
            Email(message="Please enter a valid email address."),
        ],
    )
    password = PasswordField(
        "Password", validators=[DataRequired(message="Password is required.")]
    )
    submit = SubmitField("Sign In")


class SearchForm(FlaskForm):
    query = StringField("Search activities")
    submit = SubmitField("Search")


class FilterForm(FlaskForm):
    sports_checkbox = BooleanField("Sports")
    non_sports_checkbox = BooleanField(NON_SPORTS_ACTIVITY_TYPE)
    submit = SubmitField("Filter")


class HostForm(FlaskForm):
    activity_name = StringField(
        "Activity Name",
        validators=[
            DataRequired(),
            Length(
                min=2,
                max=50,
                message="Activity name must be between 2 and 50 characters",
            ),
        ],
    )
    activity_type = SelectField(
        "Type",
        choices=[
            ("", "Select Activity Type"),
            ("Sports", "Sports"),
            (NON_SPORTS_ACTIVITY_TYPE, NON_SPORTS_ACTIVITY_TYPE),
        ],
        validators=[DataRequired()],
    )
    skills_req = StringField(
        "Required Skills",
        validators=[
            DataRequired(),
            Length(
                min=2,
                max=100,
                message="Required skills must be between 2 and 100 characters",
            ),
        ],
    )
    date = DateTimeLocalField(
        "Date", format="%Y-%m-%dT%H:%M", validators=[DataRequired()]
    )
    location = StringField(
        "Location",
        validators=[
            DataRequired(),
            Length(
                min=2, max=50, message="Location must be between 2 and 50 characters"
            ),
        ],
    )
    max_pax = IntegerField(
        "Max Participants", validators=[DataRequired(), NumberRange(min=1)]
    )
    submit = SubmitField("Host")

    def validate_date(self, field):
        if field.data < datetime.now():
            raise ValidationError("Date cannot be in the past.")


class JoinForm(FlaskForm):
    activity_id = HiddenField(validators=[DataRequired()])
    submit = SubmitField("Join")


class PostForm(FlaskForm):
    content = TextAreaField(
        "Share something with your buddies…",
        validators=[
            DataRequired(),
            Length(max=255, message="Content must be less than 255 characters"),
        ],
    )
    image = FileField(
        "Image (optional)",
        validators=[FileAllowed(["jpg", "jpeg", "png"], "Images only!")],
    )
    submit = SubmitField("Post")


class CommentForm(FlaskForm):
    comment = StringField(
        "Write a comment…",
        validators=[
            DataRequired(),
            Length(max=255, message="Comment must be less than 255 characters"),
        ],
    )
    submit = SubmitField("Post")


class ProfileEditForm(FlaskForm):
    name = StringField(
        "Name",
        validators=[
            DataRequired(),
            Length(max=50, message="Name must be less than 50 characters"),
        ],
    )
    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email(),
            Length(max=254, message="Email must be less than 254 characters"),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            Optional(),
            Length(min=8, max=255, message=PASSWORD_LENGTH_MESSAGE),
        ],
    )
    profile_picture = FileField(
        "Profile Picture",
        validators=[FileAllowed(["jpg", "jpeg", "png"], "Images only!")],
    )
    remove_profile_picture = BooleanField("Remove current profile picture")
    submit = SubmitField(SAVE_CHANGES_MESSAGE)


class ActivityEditForm(FlaskForm):
    activity_id = HiddenField()
    activity_name = StringField(
        "Activity Name",
        validators=[
            DataRequired(),
            Length(
                min=2,
                max=50,
                message="Activity name must be between 2 and 50 characters",
            ),
        ],
    )
    activity_type = SelectField(
        "Type",
        choices=[
            ("Sports", "Sports"),
            (NON_SPORTS_ACTIVITY_TYPE, NON_SPORTS_ACTIVITY_TYPE),
        ],
        validators=[DataRequired()],
    )
    skills_req = StringField(
        "Skills Required",
        validators=[
            DataRequired(),
            Length(
                min=2,
                max=100,
                message="Skills required must be between 2 and 100 characters",
            ),
        ],
    )
    date = DateTimeLocalField(
        "Date", validators=[DataRequired()], format="%Y-%m-%dT%H:%M"
    )
    location = StringField(
        "Location",
        validators=[
            DataRequired(),
            Length(
                min=2, max=50, message="Location must be between 2 and 50 characters"
            ),
        ],
    )
    max_pax = IntegerField(
        "Max Participants",
        validators=[
            DataRequired(),
            NumberRange(min=1, message="Max participants must be at least 1"),
        ],
    )
    submit = SubmitField(SAVE_CHANGES_MESSAGE)

    def validate_date(self, field):
        if field.data < datetime.now():
            raise ValidationError("Date cannot be in the past.")


class PostEditForm(FlaskForm):
    post_id = HiddenField()
    content = TextAreaField(
        "Content",
        validators=[
            DataRequired(),
            Length(max=255, message="Content must be less than 255 characters"),
        ],
    )
    remove_image = BooleanField("Remove image from post")
    submit = SubmitField(SAVE_CHANGES_MESSAGE)


class DeleteForm(FlaskForm):
    submit = SubmitField("Delete")


class DeleteActivityForm(FlaskForm):
    activity_id = HiddenField("Activity ID", validators=[DataRequired()])
    submit = SubmitField("Delete Activity")


class DeletePostForm(FlaskForm):
    post_id = HiddenField(validators=[DataRequired()])
    submit = SubmitField("Delete Post")


class OTPForm(FlaskForm):
    otp_code = StringField(
        "OTP Code",
        validators=[
            DataRequired(),
            Length(min=6, max=6, message="Enter the 6-digit code."),
        ],
        render_kw={"maxlength": 6, "autocomplete": "one-time-code"},
    )
    submit = SubmitField("Verify")


class RequestResetForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Request Password Reset")


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "New Password",
        validators=[
            DataRequired(),
            Length(min=8, max=255, message=PASSWORD_LENGTH_MESSAGE),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Reset Password")


class DisableOTPForm(FlaskForm):
    submit = SubmitField("Disable 2FA")
