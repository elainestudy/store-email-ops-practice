from http import HTTPStatus

from flask import Flask, jsonify
from pydantic import ValidationError


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError):
        details = [
            {
                "field": ".".join(str(part) for part in item["loc"]),
                "message": item["msg"],
            }
            for item in error.errors()
        ]

        return (
            jsonify(
                {
                    "error": "Validation failed",
                    "details": details,
                }
            ),
            HTTPStatus.BAD_REQUEST,
        )
