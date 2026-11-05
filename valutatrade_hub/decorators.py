import functools
import inspect
import logging

logger = logging.getLogger("valutatrade")

def log_action(action_name, verbose=False):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                bound = inspect.signature(func).bind(self, *args, **kwargs)
                params = bound.arguments
            except TypeError as e:
                logger.error(
                    f"{action_name} user='unknown' result=ERROR error_type=TypeError "
                    f"error_message='{e}'"
                )
                raise

            username = params.get("username")
            user_id = params.get("user_id")
            currency = params.get("currency")
            amount = params.get("amount")

            try:
                ret_val = func(self, *args, **kwargs)
                
                if action_name in ("REGISTER", "LOGIN"):
                    log_string = (
                        f"{action_name} user_id={ret_val} "
                        f"user_name='{username}' result=OK"
                    )
                elif action_name in ("BUY", "SELL"):
                    if verbose:
                        log_string = (
                            f"{action_name} user_id={user_id} "
                            f"currecy='{currency}' amount={amount} "
                            f"rate={ret_val.get('rate')} "
                            f"revenue={ret_val.get('revenue')} "
                            f"prev_qty={ret_val.get('prev_qty')} "
                            f"new_qty={ret_val.get('new_qty')} result=OK"
                        )
                    else:
                        log_string = (
                            f"{action_name} user_id={user_id} "
                            f"currecy='{currency}' amount={amount} "
                            f"rate={ret_val.get('rate')} "
                            f"revenue={ret_val.get('revenue')} "
                            f"result=OK"
                        )
                logger.info(log_string)
                return ret_val

            except Exception as e:
                if action_name in ("REGISTER", "LOGIN"):
                    log_string = (
                        f"{action_name} user_name='{username}' result=ERROR "
                        f"error_type={type(e).__name__} error_message='{e}'"
                    )
                elif action_name in ("BUY", "SELL"):
                    log_string = (
                        f"{action_name} user_id={user_id} "
                        f"currecy='{currency}' amount={amount} result=ERROR "
                        f"error_type={type(e).__name__} error_message='{e}'"
                    )
                logger.error(log_string)
                raise
        return wrapper
    return decorator
