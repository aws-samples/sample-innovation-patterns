# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Utility functions for working with Jinja2 templates."""

import os
from typing import Any, Optional

import jinja2
from loguru import logger


class JinjaUtil:
    """Utility class for Jinja2 template rendering operations."""

    @staticmethod
    def render(
        template: Optional[str] = None,
        template_path: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Render a Jinja2 template with the provided context variables.

        Args:
            template: Template string to render (optional)
            template_path: Path to template file to render (optional)
            **kwargs: Context variables to pass to the template

        Returns:
            Rendered template as a string

        Raises:
            ValueError: If neither template nor template_path is provided, or if both are provided
            FileNotFoundError: If template_path is provided but file doesn't exist
            jinja2.TemplateError: If template rendering fails
        """
        # Validate input parameters
        if template is None and template_path is None:
            raise ValueError("Either template string or template_path must be provided")

        if template is not None and template_path is not None:
            raise ValueError(
                "Only one of template string or template_path should be provided, not both"
            )

        try:
            if template is not None:
                # Render from template string
                logger.debug("Rendering template from string")
                # Enable auto-escaping unconditionally for security (mitigates XSS)
                environment = jinja2.Environment(  # nosemgrep: direct-use-of-jinja2 — autoescape enabled
                    autoescape=True,
                )
                jinja_template = environment.from_string(template)

            else:
                # Render from template file
                logger.debug(f"Rendering template from file: {template_path}")

                # Check if file exists
                if not os.path.exists(template_path):
                    raise FileNotFoundError(f"Template file not found: {template_path}")

                # Get directory and filename for Jinja2 FileSystemLoader
                template_dir = os.path.dirname(os.path.abspath(template_path))
                template_filename = os.path.basename(template_path)

                # Create environment with FileSystemLoader
                environment = jinja2.Environment(  # nosemgrep: direct-use-of-jinja2 — autoescape enabled
                    loader=jinja2.FileSystemLoader(template_dir),
                    # Enable auto-escaping unconditionally for security (mitigates XSS)
                    autoescape=True,
                )
                jinja_template = environment.get_template(template_filename)

            # Render the template with provided context
            logger.debug(f"Rendering template with context keys: {list(kwargs.keys())}")
            rendered_content = jinja_template.render(**kwargs)

            logger.debug("Template rendering completed successfully")
            return rendered_content

        except jinja2.TemplateError as e:
            logger.error(f"Jinja2 template error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error during template rendering: {str(e)}")
            raise
