module default {
  abstract type Auditable {
    required property created_at -> datetime {
      readonly := true;
      default := datetime_current();
    }
  }
  scalar type StatusType extending enum<in_progress, completed, error>;
  type Job extending Auditable {
    required property threads -> int16;
    required property status -> StatusType;
    property input_urls -> array<str>;
    property image_urls -> array<str>;
  }
}


# todo add required status with default as enum