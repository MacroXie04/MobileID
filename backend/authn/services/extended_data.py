from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from typing import Any, Dict, Optional, List
import json
import jsonpatch
from authn.models import UserExtendedData, QuickAction, UserChangeLog


class UserExtendedDataService:
    """Service class for managing UserExtendedData CRUD operations"""
    
    @staticmethod
    def get_or_create_extended_data(user: User) -> UserExtendedData:
        """Get or create UserExtendedData for a user"""
        extended_data, created = UserExtendedData.objects.get_or_create(user=user)
        return extended_data
    
    @staticmethod
    def get_extended_data(user: User) -> Dict[str, Any]:
        """Get extended data dictionary for a user"""
        try:
            extended_data = UserExtendedData.objects.get(user=user)
            return extended_data.extended_data
        except UserExtendedData.DoesNotExist:
            return {}
    
    @staticmethod
    def get_field_value(user: User, field_name: str, default: Any = None) -> Any:
        """Get a specific field value from extended data"""
        extended_data = UserExtendedDataService.get_extended_data(user)
        return extended_data.get(field_name, default)
    
    @staticmethod
    @transaction.atomic
    def set_field_value(
        user: User, 
        field_name: str, 
        value: Any,
        staff_user: Optional[User] = None,
        change_description: str = ""
    ) -> UserExtendedData:
        """Set a specific field value in extended data"""
        extended_data = UserExtendedDataService.get_or_create_extended_data(user)
        
        # Store the data before change
        data_before = extended_data.extended_data.copy()
        
        # Update the field
        extended_data.extended_data[field_name] = value
        extended_data.save()
        
        # Log the change if staff_user is provided
        if staff_user:
            UserExtendedDataService._log_change(
                staff_user=staff_user,
                target_user=user,
                data_before=data_before,
                data_after=extended_data.extended_data,
                change_description=change_description or f"Set {field_name} to {value}"
            )
        
        return extended_data
    
    @staticmethod
    @transaction.atomic
    def update_fields(
        user: User,
        fields: Dict[str, Any],
        staff_user: Optional[User] = None,
        change_description: str = ""
    ) -> UserExtendedData:
        """Update multiple fields in extended data"""
        extended_data = UserExtendedDataService.get_or_create_extended_data(user)
        
        # Store the data before change
        data_before = extended_data.extended_data.copy()
        
        # Update multiple fields
        extended_data.extended_data.update(fields)
        extended_data.save()
        
        # Log the change if staff_user is provided
        if staff_user:
            UserExtendedDataService._log_change(
                staff_user=staff_user,
                target_user=user,
                data_before=data_before,
                data_after=extended_data.extended_data,
                change_description=change_description or f"Updated fields: {', '.join(fields.keys())}"
            )
        
        return extended_data
    
    @staticmethod
    @transaction.atomic
    def delete_field(
        user: User,
        field_name: str,
        staff_user: Optional[User] = None,
        change_description: str = ""
    ) -> UserExtendedData:
        """Delete a specific field from extended data"""
        extended_data = UserExtendedDataService.get_or_create_extended_data(user)
        
        # Store the data before change
        data_before = extended_data.extended_data.copy()
        
        # Delete the field if it exists
        if field_name in extended_data.extended_data:
            del extended_data.extended_data[field_name]
            extended_data.save()
            
            # Log the change if staff_user is provided
            if staff_user:
                UserExtendedDataService._log_change(
                    staff_user=staff_user,
                    target_user=user,
                    data_before=data_before,
                    data_after=extended_data.extended_data,
                    change_description=change_description or f"Deleted field: {field_name}"
                )
        
        return extended_data
    
    @staticmethod
    @transaction.atomic
    def delete_fields(
        user: User,
        field_names: List[str],
        staff_user: Optional[User] = None,
        change_description: str = ""
    ) -> UserExtendedData:
        """Delete multiple fields from extended data"""
        extended_data = UserExtendedDataService.get_or_create_extended_data(user)
        
        # Store the data before change
        data_before = extended_data.extended_data.copy()
        
        # Delete multiple fields
        deleted_fields = []
        for field_name in field_names:
            if field_name in extended_data.extended_data:
                del extended_data.extended_data[field_name]
                deleted_fields.append(field_name)
        
        if deleted_fields:
            extended_data.save()
            
            # Log the change if staff_user is provided
            if staff_user:
                UserExtendedDataService._log_change(
                    staff_user=staff_user,
                    target_user=user,
                    data_before=data_before,
                    data_after=extended_data.extended_data,
                    change_description=change_description or f"Deleted fields: {', '.join(deleted_fields)}"
                )
        
        return extended_data
    
    @staticmethod
    @transaction.atomic
    def clear_all_data(
        user: User,
        staff_user: Optional[User] = None,
        change_description: str = ""
    ) -> UserExtendedData:
        """Clear all extended data for a user"""
        extended_data = UserExtendedDataService.get_or_create_extended_data(user)
        
        # Store the data before change
        data_before = extended_data.extended_data.copy()
        
        # Clear all data
        extended_data.extended_data = {}
        extended_data.save()
        
        # Log the change if staff_user is provided
        if staff_user:
            UserExtendedDataService._log_change(
                staff_user=staff_user,
                target_user=user,
                data_before=data_before,
                data_after=extended_data.extended_data,
                change_description=change_description or "Cleared all extended data"
            )
        
        return extended_data
    
    @staticmethod
    @transaction.atomic
    def apply_quick_action(
        user: User,
        action_name: str,
        staff_user: Optional[User] = None
    ) -> UserExtendedData:
        """Apply a quick action to user's extended data"""
        try:
            quick_action = QuickAction.objects.get(action_name=action_name)
        except QuickAction.DoesNotExist:
            raise ValueError(f"Quick action '{action_name}' not found")
        
        extended_data = UserExtendedDataService.get_or_create_extended_data(user)
        
        # Store the data before change
        data_before = extended_data.extended_data.copy()
        
        # Apply JSON patch
        patch = jsonpatch.JsonPatch(quick_action.json_patch)
        extended_data.extended_data = patch.apply(extended_data.extended_data)
        extended_data.save()
        
        # Log the change if staff_user is provided
        if staff_user:
            UserExtendedDataService._log_change(
                staff_user=staff_user,
                target_user=user,
                data_before=data_before,
                data_after=extended_data.extended_data,
                change_description=f"Applied quick action: {quick_action.action_name} - {quick_action.action_description}"
            )
        
        return extended_data
    
    @staticmethod
    def search_users_by_field(field_name: str, value: Any) -> List[User]:
        """Search users by a specific field value in extended data"""
        # Using JSONField lookups (requires PostgreSQL)
        extended_data_list = UserExtendedData.objects.filter(
            **{f"extended_data__{field_name}": value}
        )
        return [ed.user for ed in extended_data_list]
    
    @staticmethod
    def search_users_by_fields(criteria: Dict[str, Any]) -> List[User]:
        """Search users by multiple field values in extended data"""
        # Build query dynamically
        query = UserExtendedData.objects.all()
        for field_name, value in criteria.items():
            query = query.filter(**{f"extended_data__{field_name}": value})
        
        return [ed.user for ed in query]
    
    @staticmethod
    def _log_change(
        staff_user: User,
        target_user: User,
        data_before: Dict[str, Any],
        data_after: Dict[str, Any],
        change_description: str
    ):
        """Private method to log changes"""
        UserChangeLog.objects.create(
            staff_user=staff_user,
            target_user=target_user,
            change_description=change_description,
            data_before=data_before,
            data_after=data_after
        )
    
    @staticmethod
    def get_user_change_history(user: User, limit: Optional[int] = None) -> List[UserChangeLog]:
        """Get change history for a specific user"""
        query = UserChangeLog.objects.filter(target_user=user)
        if limit:
            query = query[:limit]
        return list(query)
    
    @staticmethod
    def increment_field(
        user: User,
        field_name: str,
        increment_by: int = 1,
        staff_user: Optional[User] = None,
        change_description: str = ""
    ) -> UserExtendedData:
        """Increment a numeric field in extended data"""
        current_value = UserExtendedDataService.get_field_value(user, field_name, 0)
        
        if not isinstance(current_value, (int, float)):
            raise ValueError(f"Field '{field_name}' is not numeric")
        
        new_value = current_value + increment_by
        
        return UserExtendedDataService.set_field_value(
            user=user,
            field_name=field_name,
            value=new_value,
            staff_user=staff_user,
            change_description=change_description or f"Incremented {field_name} by {increment_by}"
        )
    
    @staticmethod
    def toggle_boolean_field(
        user: User,
        field_name: str,
        staff_user: Optional[User] = None,
        change_description: str = ""
    ) -> UserExtendedData:
        """Toggle a boolean field in extended data"""
        current_value = UserExtendedDataService.get_field_value(user, field_name, False)
        
        if not isinstance(current_value, bool):
            raise ValueError(f"Field '{field_name}' is not boolean")
        
        new_value = not current_value
        
        return UserExtendedDataService.set_field_value(
            user=user,
            field_name=field_name,
            value=new_value,
            staff_user=staff_user,
            change_description=change_description or f"Toggled {field_name} to {new_value}"
        )