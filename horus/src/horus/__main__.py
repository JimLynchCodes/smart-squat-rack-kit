import sys
from horus.service import run

def main():
    print("[horus] starting...")
    try:
        run()
    except KeyboardInterrupt:
        print("\n[horus] interrupted by user")
    except Exception as e:
        print(f"\n[horus] CRITICAL ERROR: {e}")
        # This keeps the traceback visible for debugging
        import traceback
        traceback.print_exc()
    finally:
        # This block helps trigger the cleanup in service.py
        print("[horus] cleaning up and exiting.")

if __name__ == "__main__":
    main()