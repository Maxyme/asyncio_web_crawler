module default {
  abstract type Auditable {
    required property created_at -> datetime {
      readonly := true;
      default := datetime_current();
    }
  }
  type Job extending Auditable {
    property threads -> int16;
    property in_progress -> bool;
    property completed -> bool;
    property input_urls -> json;
    property image_urls -> json;
  }
}


# todo add required status with default as enum