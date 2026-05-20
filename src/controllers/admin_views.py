"""Flask-Admin model views, all protected behind Flask-Login auth."""

import os

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.form.upload import FileUploadField
from flask_login import current_user
from wtforms import validators

from src.models.main import (
    AdminUser,
    Airport,
    Artist,
    BackgroundText,
    Church,
    FAQ,
    HotelGroup,
    MediaDownload,
    PastConference,
    Podcast,
    SiteConfig,
    SocialProof,
    Speaker,
    Sponsor,
    TicketPrice,
    Ticker,
    Video,
    db,
)


# ---------------------------------------------------------------------------
# Base view — redirect to login if not authenticated
# ---------------------------------------------------------------------------

class SecureModelView(ModelView):
    """All admin model views inherit from this to require login."""

    extra_css = ['/static/css/admin_theme.css']

    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        from flask import request as flask_request
        return redirect(url_for("admin_auth.login_page", next=flask_request.url))


class SecureAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for("admin_auth.login_page"))
        return self.render(
            "admin/index.html",
            logout_url=url_for("admin_auth.logout"),
            admin_username=current_user.username,
            admin_role=current_user.role,
        )


# ---------------------------------------------------------------------------
# Model view customisations
# ---------------------------------------------------------------------------

class SpeakerAdmin(SecureModelView):
    column_list = ("sort_order", "name", "is_gen_z", "shrink", "image")
    column_sortable_list = ("sort_order", "name", "is_gen_z")
    column_searchable_list = ("name",)
    column_filters = ("is_gen_z",)
    form_columns = (
        "sort_order", "name", "image", "alt", "bio",
        "shrink", "image_x", "image_y",
        "titles_json", "orgs_json", "is_gen_z",
    )
    column_descriptions = {
        "image": "Path relative to /static, e.g. /static/img/speakers/foo.webp",
        "titles_json": 'JSON array of title strings, e.g. ["Lead Pastor, Grace City Church"]',
        "orgs_json": 'JSON array: [{"icon":"church","name":"Grace City","subtitle":"Wenatchee, WA"}]',
    }


def _sponsor_logo_path():
    return os.path.join(current_app.static_folder, "img", "sponsor_logos")


def _church_logo_path():
    return os.path.join(current_app.static_folder, "img", "churches")


class SponsorAdmin(SecureModelView):
    column_list = ("sort_order", "name", "category", "show_on_sponsor_page", "scale")
    column_sortable_list = ("sort_order", "name", "category")
    column_searchable_list = ("name",)
    column_filters = ("category", "show_on_sponsor_page")
    form_columns = (
        "sort_order", "name", "logo_upload", "category",
        "show_on_sponsor_page", "background_color", "scale",
    )
    form_extra_fields = {
        "logo_upload": FileUploadField(
            "Upload Logo",
            base_path=_sponsor_logo_path,
            allowed_extensions=["webp", "png", "jpg", "jpeg", "svg", "gif"],
            validators=[validators.Optional()],
        )
    }
    column_descriptions = {
        "logo_upload": "Upload a logo image (webp/png/jpg/svg). Will be auto-converted to WebP.",
        "scale": "1.0 = normal size. Greater than 1 = larger (e.g. 1.5 = 50% bigger). Less than 1 = smaller (e.g. 0.75 = 25% smaller).",
    }

    create_template = "admin/sponsor_form.html"
    edit_template   = "admin/sponsor_form.html"

    def render(self, template, **kwargs):
        """Inject preview context variables for the sponsor form template."""
        if template == self.create_template or template == self.edit_template:
            from flask import request as flask_request
            kwargs.setdefault("current_logo_url", None)
            kwargs.setdefault("is_edit", False)
            model_id = flask_request.args.get("id")
            if model_id:
                try:
                    model = self.get_one(model_id)
                    if model:
                        kwargs["current_logo_url"] = model.logo_url
                        kwargs["is_edit"] = True
                except Exception:
                    pass
        return super().render(template, **kwargs)

    def validate_form(self, form):
        """Reject duplicate sponsor names."""
        if not super().validate_form(form):
            return False
        name_field = getattr(form, "name", None)
        if name_field and name_field.data:
            from flask import request as flask_request
            model_id = flask_request.args.get("id")
            dup = Sponsor.query.filter(
                Sponsor.name == name_field.data.strip()
            ).first()
            if dup and (model_id is None or str(dup.id) != str(model_id)):
                name_field.errors.append(
                    f'A sponsor named "{name_field.data.strip()}" already exists.'
                )
                return False
        return True

    def on_model_change(self, form, model, is_created):
        from pathlib import Path
        from flask import current_app
        from src.services.image_optimizer import convert_to_webp

        raw = getattr(model, "logo_upload", None)
        if raw and isinstance(raw, str):
            abs_path = Path(current_app.static_folder) / "img" / "sponsor_logos" / raw
            try:
                webp_path = convert_to_webp(abs_path)
                model.logo_url = f"/static/img/sponsor_logos/{webp_path.name}"
            except Exception as exc:
                current_app.logger.warning("Logo WebP conversion failed: %s", exc)
                model.logo_url = f"/static/img/sponsor_logos/{raw}"
        super().on_model_change(form, model, is_created)


class ArtistAdmin(SecureModelView):
    column_list = ("sort_order", "name", "day", "stage", "genre")
    column_sortable_list = ("sort_order", "name", "day", "stage")
    column_searchable_list = ("name",)
    column_filters = ("day", "stage")
    form_columns = (
        "sort_order", "name", "image",
        "hero_image_x", "hero_image_y", "genre", "bio", "day", "stage",
    )
    column_descriptions = {
        "image": "Path relative to /static, e.g. /static/img/artists/foo.webp",
        "hero_image_x": "CSS background-position X, e.g. 50%",
        "hero_image_y": "CSS background-position Y, e.g. 0%",
    }


class TicketPriceAdmin(SecureModelView):
    column_list = ("sort_order", "name", "price", "highlight")
    column_sortable_list = ("sort_order", "name")
    form_columns = ("sort_order", "name", "price", "tax_total", "notes_json", "highlight")
    column_descriptions = {
        "notes_json": 'JSON array of note strings, e.g. ["VIP badge","Reserved seating"]'
    }


class VideoAdmin(SecureModelView):
    column_list = ("sort_order", "title", "url", "thumbnail_mobile")
    column_searchable_list = ("title", "url")
    form_columns = ("sort_order", "url", "title", "thumbnail_mobile")


class PodcastAdmin(SecureModelView):
    column_list = ("sort_order", "title", "url", "thumbnail_mobile")
    column_searchable_list = ("title", "url")
    form_columns = ("sort_order", "url", "title", "thumbnail_mobile")


class SocialProofAdmin(SecureModelView):
    column_list = ("sort_order", "name", "title", "is_boys")
    column_sortable_list = ("sort_order", "name")
    column_searchable_list = ("name", "title")
    column_filters = ("is_boys",)
    form_columns = ("sort_order", "name", "title", "quote", "alt", "img_json", "is_boys")
    column_descriptions = {
        "img_json": 'JSON array of image URL strings (can be empty [])',
        "is_boys": "Check if this belongs to the boys_social_proof list",
    }


class FAQAdmin(SecureModelView):
    column_list = ("sort_order", "category", "question")
    column_sortable_list = ("sort_order", "category")
    column_searchable_list = ("question", "category")
    column_filters = ("category",)
    form_columns = (
        "sort_order", "category", "question",
        "answer", "answer_html", "answer_list_json",
    )
    column_descriptions = {
        "answer": "Plain text answer (use this OR answer_html OR answer_list_json)",
        "answer_html": "HTML answer string",
        "answer_list_json": 'JSON array of strings, e.g. ["No firearms","No alcohol"]',
    }


class HotelGroupAdmin(SecureModelView):
    column_list = ("sort_order", "name", "distance", "source")
    column_filters = ("source",)
    column_searchable_list = ("name",)
    form_columns = ("sort_order", "name", "distance", "details", "hotels_json", "source")
    column_descriptions = {
        "hotels_json": 'JSON array: [{"name":"Hotel Name","link":"https://...","valid_link":true}]',
        "source": '"hotels" = hotels page, "accommodations" = accommodations page',
    }


class AirportAdmin(SecureModelView):
    column_list = ("sort_order", "name", "distance", "drive_time")
    column_searchable_list = ("name",)
    form_columns = ("sort_order", "name", "distance", "drive_time", "route_json", "notes")
    column_descriptions = {
        "route_json": 'JSON array of step strings, e.g. ["Take I-90 East","Take Exit 143"]'
    }


class PastConferenceAdmin(SecureModelView):
    column_list = ("sort_order", "year", "name", "summary")
    column_sortable_list = ("sort_order", "year", "name")
    column_searchable_list = ("name",)
    form_columns = ("sort_order", "year", "name", "summary", "videos_json")
    column_descriptions = {
        "videos_json": 'JSON array: [{"url":"https://...","title":"...","thumbnail_mobile":"..."}]'
    }


class MediaDownloadAdmin(SecureModelView):
    column_list = ("sort_order", "label", "external_id")
    column_searchable_list = ("label", "external_id")
    form_columns = ("sort_order", "external_id", "label", "assets_json")
    column_descriptions = {
        "assets_json": 'JSON array: [{"label":"...","thumb":"https://...","download":"https://..."}]'
    }


class TickerAdmin(SecureModelView):
    column_list = ("sort_order", "ticker_name", "text")
    column_filters = ("ticker_name",)
    column_searchable_list = ("text",)
    form_columns = ("sort_order", "ticker_name", "text")


class BackgroundTextAdmin(SecureModelView):
    column_list = ("sort_order", "group_name", "text")
    column_filters = ("group_name",)
    form_columns = ("sort_order", "group_name", "text")


class SiteConfigAdmin(SecureModelView):
    column_list = ("key",)
    column_searchable_list = ("key",)
    form_columns = ("key", "value_json")
    column_descriptions = {
        "value_json": "Full JSON blob for this config section (camping, invite, the_play, wives, etc.)"
    }


class ChurchAdmin(SecureModelView):
    column_list = ("sort_order", "name", "logo_bg", "active")
    column_sortable_list = ("sort_order", "name")
    column_searchable_list = ("name",)
    column_filters = ("active", "logo_bg")
    form_columns = (
        "sort_order", "name", "logo_upload",
        "background_color", "scale", "active",
    )
    form_extra_fields = {
        "logo_upload": FileUploadField(
            "Upload Logo",
            base_path=_church_logo_path,
            allowed_extensions=["webp", "png", "jpg", "jpeg", "svg", "gif"],
            validators=[validators.Optional()],
        )
    }
    column_descriptions = {
        "logo_upload": "Upload a logo image (webp/png/jpg/svg). Will be auto-converted to WebP.",
        "background_color": "Hex color for the card background, e.g. #ffffff for white. Leave blank for the default dark background.",
        "scale": "1.0 = normal size. Greater than 1 = larger (e.g. 1.5 = 50% bigger). Less than 1 = smaller.",
        "active": "Uncheck to hide this church from the public page without deleting it",
    }

    create_template = "admin/church_form.html"
    edit_template   = "admin/church_form.html"

    def render(self, template, **kwargs):
        if template in (self.create_template, self.edit_template):
            from flask import request as flask_request
            kwargs.setdefault("current_logo_url", None)
            kwargs.setdefault("is_edit", False)
            model_id = flask_request.args.get("id")
            if model_id:
                try:
                    model = self.get_one(model_id)
                    if model:
                        kwargs["current_logo_url"] = model.logo_url
                        kwargs["is_edit"] = True
                except Exception:
                    pass
        return super().render(template, **kwargs)

    def on_model_change(self, form, model, is_created):
        from pathlib import Path
        from flask import current_app
        from src.services.image_optimizer import convert_to_webp

        raw = getattr(model, "logo_upload", None)
        if raw and isinstance(raw, str):
            abs_path = Path(current_app.static_folder) / "img" / "churches" / raw
            try:
                webp_path = convert_to_webp(abs_path)
                model.logo_url = f"/static/img/churches/{webp_path.name}"
            except Exception as exc:
                current_app.logger.warning("Church logo WebP conversion failed: %s", exc)
                model.logo_url = f"/static/img/churches/{raw}"
        super().on_model_change(form, model, is_created)



class AdminUserAdmin(SecureModelView):
    """Only superadmins can manage admin users."""

    column_list = ("username", "role")
    form_columns = ("username", "password_hash", "role")
    column_descriptions = {
        "password_hash": "Enter the raw password here — it will be hashed automatically on save.",
        "role": '"superadmin" has full access including this page. "admin" has access to all other sections.',
    }

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_superadmin

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("admin_auth.login_page", next=request.url))
        flash("You need superadmin access to manage admin users.", "error")
        return redirect(url_for("admin.index"))

    def on_model_change(self, form, model, is_created):
        """Hash the password field before saving."""
        raw = form.password_hash.data
        if raw:
            model.set_password(raw)


class ChangePasswordView(BaseView):
    """Lets any logged-in admin change their own password."""

    extra_css = ['/static/css/admin_theme.css']

    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("admin_auth.login_page", next=request.url))

    @expose("/", methods=("GET", "POST"))
    def index(self):
        error = None
        success = None
        if request.method == "POST":
            current_pw = request.form.get("current_password", "")
            new_pw     = request.form.get("new_password", "")
            confirm_pw = request.form.get("confirm_password", "")

            if not current_user.check_password(current_pw):
                error = "Current password is incorrect."
            elif len(new_pw) < 8:
                error = "New password must be at least 8 characters."
            elif new_pw != confirm_pw:
                error = "New passwords do not match."
            else:
                current_user.set_password(new_pw)
                from src.models.main import db as _db
                _db.session.commit()
                success = "Password updated successfully."

        return self.render(
            "admin/change_password.html",
            error=error,
            success=success,
        )


# ---------------------------------------------------------------------------
# Admin factory
# ---------------------------------------------------------------------------

def create_admin(app) -> Admin:
    admin = Admin(
        app,
        name="Freedom Con Admin",
        index_view=SecureAdminIndexView(url="/admin"),
    )

    admin.add_view(SponsorAdmin(Sponsor, db.session, name="Sponsors", category="Content"))
    admin.add_view(ArtistAdmin(Artist, db.session, name="Artists", category="Content"))
    admin.add_view(SpeakerAdmin(Speaker, db.session, name="Speakers", category="Content"))
    admin.add_view(VideoAdmin(Video, db.session, name="Videos", category="Media"))
    admin.add_view(PodcastAdmin(Podcast, db.session, name="Podcasts", category="Media"))
    admin.add_view(MediaDownloadAdmin(MediaDownload, db.session, name="Media Downloads", category="Media"))
    admin.add_view(SocialProofAdmin(SocialProof, db.session, name="Social Proof", category="Content"))
    admin.add_view(FAQAdmin(FAQ, db.session, name="FAQs", category="Content"))
    admin.add_view(TicketPriceAdmin(TicketPrice, db.session, name="Ticket Prices", category="Content"))
    admin.add_view(HotelGroupAdmin(HotelGroup, db.session, name="Hotel Groups", category="Logistics"))
    admin.add_view(AirportAdmin(Airport, db.session, name="Airports", category="Logistics"))
    admin.add_view(PastConferenceAdmin(PastConference, db.session, name="Past Conferences", category="Content"))
    admin.add_view(ChurchAdmin(Church, db.session, name="Churches", category="Content"))
    admin.add_view(TickerAdmin(Ticker, db.session, name="Tickers", category="Site"))
    admin.add_view(BackgroundTextAdmin(BackgroundText, db.session, name="Background Text", category="Site"))
    admin.add_view(SiteConfigAdmin(SiteConfig, db.session, name="Site Config", category="Site"))
    admin.add_view(AdminUserAdmin(AdminUser, db.session, name="Admin Users", category="Site"))
    admin.add_view(ChangePasswordView(name="Change Password", endpoint="change_password", category="Site"))

    return admin
